import os
import random
import argparse
import warnings

from pytorch_lightning import seed_everything

from trainers import build_decomp_trainer
from utils import load_json


warnings.filterwarnings('ignore')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Query-by-sketch training')
    parser.add_argument('-c', '--config', help='training config file', required=True)
    parser.add_argument('-m', '--mode', default='train')
    args = parser.parse_args()

    assert args.mode in {'train', 'test'}

    config = load_json(args.config)

    seed = config.run.seed or random.randint(1, 10000)
    seed_everything(seed)

    print('Using seed: {}'.format(seed))
    print('Config: ', config)

    trainer, model = build_decomp_trainer(config, seed)

    if args.mode == 'train':
        print('Starting model training...')
        trainer.fit(model)

    elif args.mode == 'test':
        trainer.test(model)
