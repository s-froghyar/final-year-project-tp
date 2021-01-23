import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
import argparse

from .reporter import Reporter
from dataset import load_data, GtzanDataset
from baseline_cnn import CNN

def main(args):
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    reporter = Reporter('baseline', args.epochs)
    is_test = True

    # Load Data
    GTZAN = load_data(is_test=is_test)

    train_dataset = GtzanDataset(GTZAN.train_x, GTZAN.train_y, train=True)
    train_loader = DataLoader(dataset=train_dataset, batch_size=args.batch_size)

    test_dataset = GtzanDataset(GTZAN.test_x, GTZAN.test_y, train=False)
    test_loader = DataLoader(dataset=test_dataset, batch_size=args.batch_size, shuffle=True)

    # Initialize network and reporter
    model = CNN('yeet', get_report_data=True).to(device)
    reporter.record_first_batch(model, len(train_dataset), train_dataset[0][0])

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    # Train Network
    for epoch in range(args.epochs):
        print('epoch num ', epoch)
        reporter.reset_epoch_data()
        for batch_idx, (data, targets) in tqdm(enumerate(train_loader)):
            # Get data to cuda if possible
            data = data.to(device=device)
            targets = targets.to(device=device)

            # forward
            preds = model(data)
            loss = criterion(preds, targets)
            reporter.record_batch_data(preds, targets, loss)
            # backward
            optimizer.zero_grad()
            loss.backward()

            # gradient descent or adam step
            optimizer.step()
        reporter.record_epoch_data(model, epoch)
    reporter.set_post_training_values(model, train_dataset, test_dataset)

    train_num_correct, test_num_correct = reporter.report_on_model()
    print('train_num_correct', train_num_correct)
    print('test_num_correct', test_num_correct)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline CNN")

    parser.add_argument(
        "--dir",
        type=str,
        default='./saved-outputs',
        help="training directory (default: None)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        metavar="N",
        help="input batch size (default: 32)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.01,
        metavar="LR",
        help="initial learning rate (default: 0.01)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        metavar="N",
        help="number of epochs to train (default: 5)",
    )
    args = parser.parse_args()
    main(args)

