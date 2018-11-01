import json

import torch
from torch.autograd import Variable
from warpctc_pytorch import CTCLoss

import torch.nn.functional as F

import sys
### Import Data Utils ###
sys.path.append('../')

from data.bucketing_sampler import BucketingSampler, SpectrogramDatasetWithLength
from data.data_loader import AudioDataLoader, SpectrogramDataset
from decoder import GreedyDecoder
from model import DeepSpeech, supported_rnns
from params import cuda

import time

def eval_model(model, test_loader, decoder):
        start_iter = 0  # Reset start iteration for next epoch
        total_cer, total_wer = 0, 0
        model.eval()
        for i, (data) in enumerate(test_loader):  # test
            inputs, targets, input_percentages, target_sizes = data

            inputs = Variable(inputs, volatile=True)

            # unflatten targets
            split_targets = []
            offset = 0
            for size in target_sizes:
                split_targets.append(targets[offset:offset + size])
                offset += size

            if cuda:
                inputs = inputs.cuda()

            out = model(inputs)
            out = out.transpose(0, 1)  # TxNxH
            seq_length = out.size(0)
            sizes = input_percentages.mul_(int(seq_length)).int()

            decoded_output = decoder.decode(out.data, sizes)
            target_strings = decoder.process_strings(decoder.convert_to_strings(split_targets))
            wer, cer = 0, 0
            for x in range(len(target_strings)):
                wer += decoder.wer(decoded_output[x], target_strings[x]) / float(len(target_strings[x].split()))
                cer += decoder.cer(decoded_output[x], target_strings[x]) / float(len(target_strings[x]))
            total_cer += cer
            total_wer += wer

            if cuda:
                torch.cuda.synchronize()
            del out
        wer = total_wer / len(test_loader.dataset)
        cer = total_cer / len(test_loader.dataset)
        wer *= 100
        cer *= 100

        return wer, cer

class AverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

def eval_model_verbose(model, test_loader, decoder, cuda, n_trials, batches):
        start_iter = 0  # Reset start iteration for next epoch
        total_cer, total_wer = 0, 0
        model.eval()
        batch_time = AverageMeter()
        for i, (data) in enumerate(test_loader):  # test
            print(i)
            if batches != i:
                continue
            end = time.time()
            trial_i = 1
            while trial_i < n_trials:
		    inputs, targets, input_percentages, target_sizes = data

		    inputs = Variable(inputs, volatile=False)

		    # unflatten targets
		    split_targets = []
		    offset = 0
		    for size in target_sizes:
			split_targets.append(targets[offset:offset + size])
			offset += size

		    if cuda:
			inputs = inputs.cuda()

                    import pdb; pdb.set_trace()
		    out = model(inputs)
		    out = out.transpose(0, 1)  # TxNxH
		    seq_length = out.size(0)
                    print(seq_length)
		    sizes = input_percentages.mul_(int(seq_length)).int()

		    decoded_output = decoder.decode(out.data, sizes)
		    target_strings = decoder.process_strings(decoder.convert_to_strings(split_targets))
		    wer, cer = 0, 0
		    for x in range(len(target_strings)):
			wer += decoder.wer(decoded_output[x], target_strings[x]) / float(len(target_strings[x].split()))
			cer += decoder.cer(decoded_output[x], target_strings[x]) / float(len(target_strings[x]))
		    total_cer += cer
		    total_wer += wer
                    import pdb; pdb.set_trace()
		    
		    # measure elapsed time
		    batch_time.update(time.time() - end)
		    end = time.time()
		    
		    print('[{0}/{1}]\t'
			  'Time ({batch_time.avg:.3f})\t'.format(
			  (i + 1), len(test_loader), batch_time=batch_time))

		    # del loss

		    #if cuda:
		    #	torch.cuda.synchronize()
		    #del out
                    trial_i += 1
            break
        wer = total_wer / len(test_loader.dataset)
        cer = total_cer / len(test_loader.dataset)
        wer *= 100
        cer *= 100

        return wer, cer
