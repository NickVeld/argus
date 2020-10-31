import os
from pathlib import Path
from typing import Union

import torch

from argus.model.build import MODEL_REGISTRY, cast_device
from argus.utils import deep_to, device_to_str, default, identity


def load_model(file_path: Union[str, Path],
               nn_module=default,
               optimizer=default,
               loss=default,
               prediction_transform=default,
               device=default,
               change_params_func=identity,
               change_state_dict_func=identity,
               model_name=default,
               **kwargs):
    """Load an argus model from a file.

    The function allows loading an argus model, saved with
    :meth:`argus.model.Model.save`. The model is always loaded in *eval* mode.

    Args:
        file_path (str): Path to the file to load.
        device (str or :class:`torch.device`, optional): Device for the model.
            Defaults to None.
        nn_module (dict, tuple or str, optional): Params of the nn_module to
            replace params in the state.
        optimizer (dict, tuple or str, optional): Params of the optimizer to
            replace params in the state. Set to `None` if don't want to create
            optimizer in the loaded model.
        loss (dict, tuple or str, optional): Params of the loss to replace params
            in the state. Set to `None` if don't want to create loss in the
            loaded model.
        prediction_transform (dict, tuple or str, optional): Params of the
            prediction_transform to replace params in the state. Set to `None`
            if don't want to create prediction_transform in the loaded model.
        change_params_func (function, optional): Function for modification of
            state params. Takes as input params from the loaded state, outputs
            params to model creation.
        change_state_dict_func (function, optional): Function for modification of
            nn_module state dict. Takes as input state dict from the loaded
            state, outputs state dict to model creation.
        model_name (str): Class name of :class:`argus.model.Model`.
            By default uses name from loaded state.

    Raises:
        ImportError: If the model is not available in the scope. Often it means
            that it is not imported or defined.
        FileNotFoundError: If the file is not found by the *file_path*.

    Returns:
        :class:`argus.model.Model`: Loaded argus model.

    """

    if os.path.isfile(file_path):
        state = torch.load(file_path)

        if model_name is default:
            model_name = state['model_name']
        else:
            model_name = model_name

        if model_name in MODEL_REGISTRY:
            params = state['params']
            if device is not default:
                device = cast_device(device)
                device = device_to_str(device)
                params['device'] = device

            if nn_module is not default:
                if nn_module is None:
                    raise ValueError("nn_module is required attribute for argus.Model")
                params['nn_module'] = nn_module
            if optimizer is not default:
                params['optimizer'] = optimizer
            if loss is not default:
                params['loss'] = loss
            if prediction_transform is not default:
                params['prediction_transform'] = prediction_transform

            for attribute, attribute_params in kwargs.items():
                params[attribute] = attribute_params

            model_class = MODEL_REGISTRY[model_name]
            params = change_params_func(params)
            model = model_class(params)
            nn_state_dict = deep_to(state['nn_state_dict'], model.device)
            nn_state_dict = change_state_dict_func(nn_state_dict)

            model.get_nn_module().load_state_dict(nn_state_dict)
            model.eval()
            return model
        else:
            raise ImportError(f"Model '{model_name}' not found in scope")
    else:
        raise FileNotFoundError(f"No state found at {file_path}")
