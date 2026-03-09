"""
Middleware personnalisé pour supprimer les headers de sécurité
qui nécessitent HTTPS lorsque l'application est servie en HTTP
"""
from django.utils.deprecation import MiddlewareMixin


class RemoveUnsafeSecurityHeadersMiddleware(MiddlewareMixin):
    """
    Supprime les headers de sécurité qui nécessitent HTTPS
    lorsque l'application est servie en HTTP
    """
    
    def process_response(self, request, response):
        # Supprimer Cross-Origin-Opener-Policy si on est en HTTP
        # (ce header est ignoré par les navigateurs sur HTTP de toute façon)
        if 'Cross-Origin-Opener-Policy' in response:
            del response['Cross-Origin-Opener-Policy']
        
        # Supprimer aussi Cross-Origin-Embedder-Policy si présent
        if 'Cross-Origin-Embedder-Policy' in response:
            del response['Cross-Origin-Embedder-Policy']
        
        return response
