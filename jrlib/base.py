import json
import logging
import re
import sys
import traceback
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .fields import UNDEF, BaseField

api_methods = {}

DEBUG = settings.DEBUG


@csrf_exempt
def api_dispatch(request):
    try:
        body = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return JsonResponse({'jsonrpc': '2.0',
                             'id': None,
                             'error': {'code': -32700,
                                       'message': 'Parse error'}})
    request_id = body.get('id')
    version = body.get('jsonrpc')
    if version != '2.0':
        error_text = "JSONRPC protocol version MUST be exactly '2.0'"
        return JsonResponse({'jsonrpc': '2.0',
                             'id': request_id,
                             'error': {'code': -32600,
                                       'message': 'Invalid Request',
                                       'data': {'text': error_text}}})
    api_name = body.get('method')
    if not api_name:
        error_text =\
            'Method field MUST containing the name of the method to be invoked'
        return JsonResponse({'jsonrpc': '2.0',
                             'id': request_id,
                             'error': {'code': -32600,
                                       'message': 'Invalid Request',
                                       'data': {'text': error_text}}})
    cls = api_methods.get(api_name)
    if not cls:
        return JsonResponse({'jsonrpc': '2.0',
                             'id': request_id,
                             'error': {'code': -32601,
                                       'message': 'Method not found'}})
    params = body.get('params', {})  # TODO: support params as list (not {})
    jsonrpc_response = {'jsonrpc': '2.0', 'id': request_id}
    try:
        instance = cls(params)
        if instance.result is not UNDEF:
            jsonrpc_response.update({'result': instance.result})
        else:
            jsonrpc_response.update({'error': {'code': -32603,
                                               'message': 'Internal error'}})
    except Exception as exc:
        error = {'code': -1, 'message': str(exc)}
        stack = traceback.format_exc()
        if DEBUG:
            error['data'] = {
                'stack': stack,
                'executable': sys.executable}
        logging.error('{}'.format(stack))
        jsonrpc_response.update({'error': error})
    return JsonResponse(jsonrpc_response)


class MetaBase(type):
    def __new__(self, name, bases, namespace):
        cls = super(MetaBase, self).__new__(
            self, name, bases, namespace)
        if len(cls.mro()) > 2:  # 1 - object, 2 - Method, 3 - UserCustomMethod
            api_name = cls.__name__
            api_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', api_name)
            api_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', api_name).lower()
            api_methods[api_name] = cls
        cls._fields = [key for key, val in namespace.items()
                       if isinstance(val, BaseField)]
        return cls


class Method(metaclass=MetaBase):

    def __init__(self, data, *args, **kwargs):
        print('class method init')
        self.result = UNDEF
        self.error = None
        print('M F {}'.format(self._fields))
        for key in self._fields:
            try:
                print('METHOD - {} : {}'.format(key, data.get(key)))
                setattr(self, key, data.get(key, UNDEF))
            except Exception as exc:
                raise ValueError('{}: {}'.format(key, exc))
        try:
            self.validate()
        except Exception:
            raise
        if not self.error:
            try:
                self.result = self.execute()
            except Exception:
                raise

    def validate(self):
        pass

    def execute(self):
        pass

    def _run_clean(self):
        # пока сложно реализовать, т.к. такой clean_* должен вызываться перед
        # валидацией полей, которые описаны в наследниках Field
        #
        #
        # дополнитлеьная кастомная очистка конкретных полей метода
        # например есть поле email, кастомная очистка будет
        # email = clean_email(self.email)
        # в _run_clean() будет цикл по clean_*
        # пока что этот функционал можно не делать
        pass

    # TODO: нужен ли метод clean для метода как для django-формы?

    def before(self):
        # TODO: вместо before будут декораторы, через которые можно навешивать валидаторы
        pass

    def after(self):
        # TODO: аналогично before
        pass
