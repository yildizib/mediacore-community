# This file is a part of MediaCore CE (http://www.mediacorecommunity.org),
# Copyright 2009-2013 MediaCore Inc., Felix Schwarz and other contributors.
# For the exact contribution history, see the git revision log.
# The source code contained in this file is licensed under the GPLv3 or
# (at your option) any later version.
# See LICENSE.txt in the main project directory, for more information.

import new

from decorator import decorator
from pylons import request
from pylons.controllers.util import abort

__all__ = ['ControllerProtector', 'FunctionProtector', 'has_permission', 
    'Predicate']


class Predicate(object):
    def has_required_permission(self, environ):
        raise NotImplementedError()


class has_permission(Predicate):
    def __init__(self, permission_name):
        self.permission_name = permission_name
    
    def has_required_permission(self, request):
        environ = request.environ
        # potentially wrapping the BaseController which sets up request.perm,
        # therefore we have to get the perm object from the environ
        return environ['mediacore.perm'].contains_permission(self.permission_name)


class FunctionProtector(object):
    def __init__(self, predicate):
        self.predicate = predicate
    
    def wrap(self, function):
        def _wrap(function_, *args, **kwargs):
            if self.predicate.has_required_permission(request):
                return function_(*args, **kwargs)
            is_user_authenticated = request.environ.get('repoze.who.identity')
            if is_user_authenticated:
                abort(403)
            abort(401)
        return decorator(_wrap, function)
    

class ControllerProtector(object):
    def __init__(self, predicate):
        self.predicate = predicate
    
    def __call__(self, instance):
        import inspect
        assert not inspect.isclass(instance)
        klass = instance.__class__
        before_method = self._wrap__before__(klass)
        instance.__before__ = new.instancemethod(before_method, instance, klass)
        return instance
    
    def _wrap__before__(self, klass):
        before = lambda *args, **kwargs: None
        before.__name__ = '__before__'
        if hasattr(klass, '__before__'):
            before = klass.__before__.im_func
        return FunctionProtector(self.predicate).wrap(before)


