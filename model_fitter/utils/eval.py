from torch import nn
import numpy as np
import torch
import torchaudio.transforms as aud_transforms

from .utils import *
from .tp import get_tp_loss
from .augerino import unif_aug_loss, GaussianNoiseAug, PitchShiftAug

def test_model(model, config, reporter, device, loader, epoch):
    ''' TTA '''
    if config.local:
        model = model.float()
    
    model.eval()
    chosen_aug = config.aug_params.transform_chosen

    all_targets = None
    all_predictions = None
    
    if not config.local:
        tta = tta.double()

    with torch.no_grad():
        for batch_idx, (base_data, targets) in enumerate(loader):
            preds = [get_model_prediction(model, base_data[:,i,:,:,:], device, config) for i in range(4)]
            final_predictions = get_final_preds(preds)

            reporter.record_tta(final_predictions.to(device), targets.to(device))

            if all_predictions is None:
                all_predictions = final_predictions
            else:
                all_predictions = torch.vstack((all_predictions, final_predictions))
            if all_targets is None:
                all_targets = targets
            else:
                all_targets = torch.vstack((all_targets, targets))
        reporter.save_predictions_for_cm(all_predictions, all_targets, epoch)


def report_on_model(self):
    print('\n\Getting report on model...')
    train_loader = torch.utils.data.DataLoader(self.train_set, batch_size=64)
    test_loader = torch.utils.data.DataLoader(self.test_set, batch_size=64)
    
    self.train_predictions = get_all_preds(self.model, train_loader)
    self.test_predictions = get_all_preds(self.model, test_loader)

    train_num_correct = get_num_correct(self.train_predictions, self.train_set.targets)
    test_num_correct = get_num_correct(self.test_predictions, self.test_set.targets)
    
    self.train_confusion_matrix = confusion_matrix(
                                self.train_set.targets,
                                self.train_predictions.argmax(dim=1))
    self.test_confusion_matrix = confusion_matrix(
                                self.test_set.targets,
                                self.test_predictions.argmax(dim=1))
    
    return (train_num_correct, test_num_correct)