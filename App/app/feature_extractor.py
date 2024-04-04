import torch

from networks import NormalEncoder
from networks import Encoder
from networks import Decoder


def model_state_dict(state_dict, model_name):
    new_state_dict = {}
    for key, value in state_dict.items():
        if model_name in key:
            new_key = key[len(model_name) + 1:]
            new_state_dict[new_key] = value
    return new_state_dict


class FeatureExtractor(object):

    def __init__(self, network_config, saved_model_path):
        self.network_config = network_config
        self.saved_model_path = saved_model_path

        self.init_models()

    def init_models(self):
        state_dict = torch.load(self.saved_model_path,
                                map_location=torch.device('cpu'))['state_dict']

        if self.network_config['nEncoder']['use_vae']:
            self.nEncoder = NormalEncoder(
                input_dim=self.network_config['nEncoder']['input_dim'],
                emb_dim=self.network_config['nEncoder']['emb_dim'],
                filters=self.network_config['nEncoder']['filters']
            )

        else:
            self.nEncoder = Encoder(
                input_dim=self.network_config['nEncoder']['input_dim'],
                emb_dim=self.network_config['nEncoder']['emb_dim'],
                filters=self.network_config['nEncoder']['filters']
            )

        self.nEncoder.load_state_dict(model_state_dict(state_dict, 'nEncoder'))

        self.lEncoder = Encoder(
            input_dim=self.network_config['lEncoder']['input_dim'],
            emb_dim=self.network_config['lEncoder']['emb_dim'],
            filters=self.network_config['lEncoder']['filters']
        )

        self.lEncoder.load_state_dict(model_state_dict(state_dict, 'lEncoder'))

        if self.network_config['aEncoder']['use_vae']:
            self.aEncoder = NormalEncoder(
                input_dim=self.network_config['aEncoder']['input_dim'],
                emb_dim=self.network_config['aEncoder']['emb_dim'],
                filters=self.network_config['aEncoder']['filters']
            )
        else:
            self.aEncoder = Encoder(
                input_dim=self.network_config['aEncoder']['input_dim'],
                emb_dim=self.network_config['aEncoder']['emb_dim'],
                filters=self.network_config['aEncoder']['filters']
            )

        self.aEncoder.load_state_dict(model_state_dict(state_dict, 'aEncoder'))

        if 'iDecoder' in self.network_config.keys():
            self.iDecoder = Decoder(
                output_dim=self.network_config['iDecoder']['output_dim'],
                emb_dim=self.network_config['iDecoder']['emb_dim'],
                filters=self.network_config['iDecoder']['filters'],
            )

            self.iDecoder.load_state_dict(
                model_state_dict(state_dict, 'iDecoder'))

        if 'lDecoder' in self.network_config.keys():
            self.lDecoder = Decoder(
                output_dim=self.network_config['lDecoder']['output_dim'],
                emb_dim=self.network_config['lDecoder']['emb_dim'],
                filters=self.network_config['lDecoder']['filters'],
            )

            self.lDecoder.load_state_dict(
                model_state_dict(state_dict, 'lDecoder'))

    def preprocess(self, image, label=None):
        image = torch.from_numpy(image).float().unsqueeze(0)
        if not label is None:
            label = torch.from_numpy(label).float().unsqueeze(0).unsqueeze(0)
        return image, label

    def to_code(self, tensor):
        return tensor.squeeze(0).cpu().detach().numpy().flatten()

    def extract_feature(self, template_image, sketch_image):
        with torch.no_grad():
            image, label = self.preprocess(template_image, sketch_image)

            self.nEncoder.eval()
            self.lEncoder.eval()

            nac = self.to_code(self.nEncoder(image))
            aac = self.to_code(self.lEncoder(label))

            eac = (nac + aac)

        return eac, nac, aac

    def extract_anatomy_code(self, input_image):
        with torch.no_grad():
            image, label = self.preprocess(input_image)

            self.nEncoder.eval()
            self.aEncoder.eval()

            nac = self.to_code(self.nEncoder(image))
            aac = self.to_code(self.aEncoder(image))

            eac = (nac + aac)

        return eac, nac, aac
