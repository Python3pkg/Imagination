# v2
import re

from ..meta.container  import Entity, Factorization, Lambda

_re_factorization_element_name = re.compile('^factori(s|z)ation$')


class AbstractContainerCreator(object):
    @staticmethod
    def can_handle(container_type):
        raise NotImplementedError()

    @staticmethod
    def create(container_id, container_params, interceptions, container_node):
        raise NotImplementedError()


class EntityCreator(AbstractContainerCreator):
    @staticmethod
    def can_handle(container_type):
        return container_type == 'entity'

    @staticmethod
    def create(container_id, container_params, interceptions, container_node):
        return Entity(
            container_id,
            container_node.attribute('class') or None,
            container_params,
            interceptions
        )


class FactorizationCreator(AbstractContainerCreator):
    @staticmethod
    def can_handle(container_type):
        return _re_factorization_element_name.search(container_type)

    @staticmethod
    def create(container_id, container_params, interceptions, container_node):
        return Factorization(
            container_id,
            container_node.attribute('with'),
            container_node.attribute('call'),
            container_params,
            interceptions
        )


class LambdaCreator(AbstractContainerCreator):
    @staticmethod
    def can_handle(container_type):
        return container_type == 'callable'

    @staticmethod
    def create(container_id, container_params, interceptions, container_node):
        return Lambda(
            container_id,
            container_node.attribute('with'),
            container_params
        )
