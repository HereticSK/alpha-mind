# -*- coding: utf-8 -*-
"""
Created on 2017-5-10

@author: cheng.li
"""

import base64
import pickle
import numpy as np
import arrow
from distutils.version import LooseVersion
from sklearn import __version__ as sklearn_version
from sklearn.linear_model import LinearRegression as LinearRegressionImpl
from PyFin.api import pyFinAssert
from alphamind.model.modelbase import ModelBase
from alphamind.utilities import alpha_logger


class ConstLinearModel(ModelBase):

    def __init__(self,
                 features: list=None,
                 weights: np.ndarray=None):
        super().__init__(features)
        if features is not None and weights is not None:
            pyFinAssert(len(features) == len(weights),
                        ValueError,
                        "length of features is not equal to length of weights")
            self.weights = np.array(weights).flatten()

    def fit(self, x: np.ndarray, y: np.ndarray):
        pass

    def predict(self, x):
        return x @ self.weights

    def save(self):
        model_desc = super().save()
        model_desc['weight'] = list(self.weights)
        return model_desc

    @classmethod
    def load(cls, model_desc: dict):
        obj_layout = cls()
        obj_layout.features = model_desc['features']
        obj_layout.weights = np.array(model_desc['weight'])
        return obj_layout


class LinearRegression(ModelBase):

    def __init__(self, features: list=None, fit_intercept: bool=False):
        super().__init__(features)
        self.impl = LinearRegressionImpl(fit_intercept=fit_intercept)
        self.trained_time = None

    def fit(self, x: np.ndarray, y: np.ndarray):
        self.impl.fit(x, y)
        self.trained_time = arrow.now().format("YYYY-MM-DD HH:mm:ss")

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.impl.predict(x)

    def save(self) -> dict:
        model_desc = super().save()
        model_desc['internal_model'] = self.impl.__class__.__module__ + "." + self.impl.__class__.__name__
        encoded = base64.encodebytes(pickle.dumps(self.impl))
        model_desc['desc'] = encoded.decode('ascii')
        model_desc['sklearn_version'] = sklearn_version
        model_desc['trained_time'] = self.trained_time
        model_desc['coef'] = self.impl.coef_[0].tolist()
        return model_desc

    def score(self) -> float:
        return self.impl.score()

    @classmethod
    def load(cls, model_desc: dict):
        obj_layout = cls()
        obj_layout.features = model_desc['features']
        obj_layout.trained_time = model_desc['trained_time']

        if LooseVersion(sklearn_version) < LooseVersion(model_desc['sklearn_version']):
            alpha_logger.warning('Current sklearn version {0} is lower than the model version {1}. '
                                 'Loaded model may work incorrectly.'.format(
                sklearn_version, model_desc['sklearn_version']))

        encoded = model_desc['desc'].encode('ascii')
        obj_layout.impl = pickle.loads(base64.decodebytes(encoded))
        return obj_layout


if __name__ == '__main__':

    import pprint
    ls = ConstLinearModel(['a', 'b'], np.array([0.5, 0.5]))

    x = np.array([[0.2, 0.2],
                  [0.1, 0.1],
                  [0.3, 0.1]])

    ls.predict(x)

    desc = ls.save()
    new_model = ConstLinearModel.load(desc)

    pprint.pprint(new_model.save())
