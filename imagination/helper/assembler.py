'''
:Author: Juti Noppornpitak

The module contains the assembler to constuct loaders and entites based on the configuration
and register to a particular locator.

The schema is defined as followed::

    # Base

    <imagination>
        ENTITY*
    </imagination>

    # Entity

    ENTITY = <entity id=ENTITY_ID class=ENTITY_CLASS [option=ENTITY_OPTIONS]?>
                 PARAMS*
                 INTERCEPTION*
             </entity>

    ENTITY_OPTIONS=(factory-mode|no-interuption)
    # Event

    EVENT=(before|pre|post|after)

    INTERCEPTION =  <interception
                        EVENT=REFERENCE_ENTITY_IDENTIFIER
                        do=REFERENCE_ENTITY_METHOD
                        with=THIS_ENTITY_METHOD>
                        PARAMETERS
                    </interception>

where:
* ENTITY_ID is the identifier of the entity.
* ENTITY_CLASS is the fully-qualified class name of the entity. (e.g. ``tori.service.rdb.EntityService``)
* ``option`` is the option of the entity where ``ENTITY_OPTIONS`` can have one
  or more of:
  * ``factory-mode``: always fork the instance of the given class.
  * ``no-interuption``: any methods of the entity cannot be interrupted.
* REFERENCE_ENTITY_IDENTIFIER is the reference's entity identifier
* REFERENCE_ENTITY_METHOD is the reference's method name
* THIS_ENTITY_METHOD is this entity's method name
* EVENT is where the REFERENCE_ENTITY_METHOD is intercepted.
  * 'before' is an event before the execution of the method of the reference
    (reference method) regardless to the given arguments to the reference
    method.
  * 'pre' is an event on pre-contact of the reference method and concerning
    about the arguments given to the reference method. The method of the entity
    (the intercepting method) takes the same paramenter as the reference method.
  * 'post' is an event on post-contact of the reference method and concerning
    about the result returned by the reference method. The intercepting method
    for this event takes only one parameter which is the result from the
    reference method or any previous post-contact interceptors.
  * 'after' is an event after the execution of the reference method regardless
    to the result reterned by the reference method.

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <!--
    This is specific for the test of dependency injection on actionable events and
    super lazy loaders allowing any arbitery order of entity declaration.
    -->
    <imagination>
        <entity id="alpha" class="dummy.lazy_action.Alpha">
            <param type="entity" name="accompany">beta</param>
            <interception before="charlie" do="cook" with="order">
                <param type="unicode" name="item">egg and becon</param>
            </interception>
            <interception pre="charlie" do="repeat" with="confirm"/>
            <interception before="charlie" do="serve" with="speak_to_accompany">
                <param type="str" name="context">watch your hand</param>
            </interception>
            <interception before="charlie" do="serve" with="wash_hands"/>
            <interception after="me" do="eat" with="speak">
                <param type="str" name="context">merci</param>
            </interception>
        </entity>
        <entity id="beta" class="dummy.lazy_action.Beta"/>
        <entity id="charlie" class="dummy.lazy_action.Charlie"/>
    </imagination>

.. note::
    Copyright (c) 2012 Juti Noppornpitak

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
    of the Software, and to permit persons to whom the Software is furnished to do
    so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''

from re import split

from kotoba.kotoba import Kotoba
from kotoba        import load_from_file

from imagination.decorator.validator import restrict_type
from imagination.entity              import Entity
from imagination.exception           import *
from imagination.loader              import Loader
from imagination.helper.data         import *
from imagination.meta.interception   import Interception
from imagination.meta.package        import Parameter
from imagination.proxy               import Proxy

class Assembler(object):
    '''
    :param `transformer`: an instance of :class:`imagination.helper.data.Transformer`
    '''

    __known_interceptable_events = ['before', 'pre', 'post', 'after']

    @restrict_type(Transformer)
    def __init__(self, transformer):
        self.__interceptions = []
        self.__transformer   = transformer
        self.__known_proxies = {}

    @restrict_type(unicode)
    def load(self, filepath):
        xml = load_from_file(filepath)

        # First, register proxies to entities (for lazy initialization).
        for node in xml.children():
            self.__validate_node(node)
            self.__register_proxy(node)

        # Then, register loaders for entities.
        for node in xml.children():
            self.__get_interceptions(node)
            self.__register_loader(node)

        # Then, declare interceptions to target entities.
        for interception in self.__interceptions:
            self.locator()\
                .get_wrapper(interception.actor.id())\
                .register_interception(interception)

    def locator(self):
        return self.__transformer.locator()

    @restrict_type(Kotoba)
    def __validate_node(self, node):
        if not node.attribute('id'):
            raise IncompatibleBlockError, 'Invalid entity configuration. No ID specified.'

        if not node.attribute('class'):
            raise IncompatibleBlockError, 'Invalid entity configuration. No class type specified.'

    @restrict_type(Kotoba)
    def __register_proxy(self, node):
        id    = node.attribute('id')
        proxy = Proxy(self.locator(), id)

        self.locator().set(id, proxy)

        # this is for interceptors
        self.__known_proxies[id] = proxy

    @restrict_type(Kotoba)
    def __register_loader(self, node):
        id     = node.attribute('id')
        kind   = node.attribute('class')
        params = self.__get_params(node)
        tags   = self.__get_tags(node)

        loader = Loader(kind)

        entity = Entity(id, loader, *params.largs, **params.kwargs)
        entity.tags(tags)

        self.locator().set(id, entity)

    @restrict_type(Kotoba)
    def __get_tags(self, node):
        tags = node.attribute('tags')

        return tags and split(' ', tags.strip()) or []

    @restrict_type(Kotoba)
    def __get_interceptions(self, node):
        for sub_node in node.children('interception'):
            self.__interceptions.append(self.__get_interception(sub_node))

    @restrict_type(Kotoba)
    def __get_interception(self, node):
        actor = None
        event = None

        intercepted_action = None
        handling_action    = None

        for given_event in self.__known_interceptable_events:
            given_actor = node.attribute(given_event)

            # If the actor is not defined, continue or if the event is already
            # set (in the earlier iteration), raise the exception.
            if not given_actor:
                continue
            elif event:
                raise MultipleInterceptingEventsWarning, given_event

            # Initially get the name of the actor and the handler.
            actor   = given_actor
            handler = node.parent().attribute('id')

            if actor == Interception.self_reference_keyword():
                actor = handler

            # If the actor or the handler has no proxies, raise the exception.
            if actor not in self.__known_proxies:
                raise UnknownProxyError, 'The target (%s) of the interception is unknown.' % actor

            if handler not in self.__known_proxies:
                raise UnknownProxyError, 'The handler (%s) of the interception is unknown.' % handler

            actor   = self.__known_proxies[actor]
            handler = self.__known_proxies[handler]
            event   = given_event

            intercepted_action  = node.attribute('do')
            handling_action     = node.attribute('with')
            handling_parameters = self.__get_params(node)

        return Interception(
            event,
            actor,
            intercepted_action,
            handler,
            handling_action,
            handling_parameters
        )

    @restrict_type(Kotoba)
    def __get_params(self, node):
        package = Parameter()

        index = 0

        for param in node.children('param'):
            try:
                assert param.attribute('name')\
                    or param.attribute('type'),\
                    'The parameter #%d does not have either name or type.' % index
            except AssertionError, e:
                raise IncompatibleBlockError, e.message

            index += 1
            name   = param.attribute('name')

            if package.kwargs.has_key(name):
                raise DuplicateKeyWarning, 'There is a parameter name "%s" with that name already registered.' % name
                pass

            package.kwargs[name] = self.__transformer.cast(
                param.data(),
                param.attribute('type')
            )

        return package
