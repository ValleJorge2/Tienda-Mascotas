# endpoints/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import get_resolver
from rest_framework import status
import inspect

class EndpointListView(APIView):
    """
    View to list all available API endpoints
    """
    def get(self, request):
        resolver = get_resolver()
        endpoints = {}
        
        def get_view_name(callback):
            """Helper function to get view name"""
            if callback is None:
                return 'NoneType'
            if inspect.isclass(callback):
                return callback.__name__
            if hasattr(callback, 'view_class'):
                return callback.view_class.__name__
            if hasattr(callback, '__class__'):
                return callback.__class__.__name__
            return str(callback)

        def get_methods(callback):
            """Helper function to get HTTP methods"""
            methods = set()
            
            # ViewSet actions
            if hasattr(callback, 'actions'):
                methods.update(method.upper() for method in callback.actions.keys())
            
            # Class-based views
            if hasattr(callback, 'view_class'):
                view_class = callback.view_class
                for method in ['get', 'post', 'put', 'patch', 'delete']:
                    if hasattr(view_class, method):
                        methods.add(method.upper())
            
            # Function-based views
            if inspect.isfunction(callback):
                if hasattr(callback, 'view_class'):
                    view_class = callback.view_class
                    methods.update(method.upper() for method in getattr(view_class, 'http_method_names', []))
            
            # Default to GET if no methods found
            return list(methods) if methods else ['GET']

        def format_path(path):
            """Format the URL path"""
            # Remove regex patterns and format to a readable URL
            path = str(path).replace('^', '').replace('$', '')
            if not path.startswith('/'):
                path = '/' + path
            if not path.startswith('/api'):
                path = '/api' + path
            return path

        def process_pattern(pattern, prefix=''):
            """Process a single URL pattern"""
            if hasattr(pattern, 'pattern'):
                # Get the full path
                full_path = format_path(prefix + str(pattern.pattern))
                
                # Only process API endpoints
                if not full_path.startswith('/api/'):
                    return
                
                # Get the app name from the path
                parts = full_path.split('/')
                app_name = parts[2] if len(parts) > 2 and parts[2] else 'root'
                
                if app_name not in endpoints:
                    endpoints[app_name] = []
                
                # Get view information
                if hasattr(pattern, 'callback'):
                    view_name = get_view_name(pattern.callback)
                    methods = get_methods(pattern.callback)
                    
                    endpoint_info = {
                        'path': full_path,
                        'view': view_name,
                        'methods': methods,
                        'name': pattern.name if hasattr(pattern, 'name') else None
                    }
                    
                    # Add only if not duplicate
                    if not any(e['path'] == full_path and e['methods'] == methods 
                             for e in endpoints[app_name]):
                        endpoints[app_name].append(endpoint_info)

        def collect_urls(url_patterns, prefix=''):
            """Recursively collect URL patterns"""
            for pattern in url_patterns:
                if hasattr(pattern, 'url_patterns'):
                    # URL patterns group
                    new_prefix = prefix
                    if hasattr(pattern, 'pattern'):
                        new_prefix = prefix + str(pattern.pattern)
                    collect_urls(pattern.url_patterns, new_prefix)
                else:
                    # Single URL pattern
                    process_pattern(pattern, prefix)

        # Start URL collection
        collect_urls(resolver.url_patterns)
        
        # Remove empty sections and sort endpoints
        filtered_endpoints = {
            k: sorted(v, key=lambda x: x['path'])
            for k, v in endpoints.items()
            if v and k not in ['', 'admin']
        }

        if not filtered_endpoints:
            # Debug information
            debug_info = {
                'url_patterns_count': len(resolver.url_patterns),
                'detected_patterns': [
                    {
                        'pattern': str(pattern.pattern) if hasattr(pattern, 'pattern') else 'no pattern',
                        'has_callback': hasattr(pattern, 'callback'),
                        'has_url_patterns': hasattr(pattern, 'url_patterns'),
                    }
                    for pattern in resolver.url_patterns
                ]
            }
            return Response({
                'message': 'Available API Endpoints (Debug Mode)',
                'endpoints': filtered_endpoints,
                'debug_info': debug_info
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Available API Endpoints',
            'endpoints': filtered_endpoints
        }, status=status.HTTP_200_OK)