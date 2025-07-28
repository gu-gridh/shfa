from django.conf import settings

# IIIF Configuration
IIIF_CONFIG = {
    'BASE_URL': getattr(settings, 'API_BASE_URL', 'https://diana.dh.gu.se/diana/static/'),
    'IIIF_URL': getattr(settings, 'IIIF_BASE_URL', 'https://img.dh.gu.se/diana/static/'),
    'SITE_URL': getattr(settings, 'SITE_URL', 'https://shfa.dh.gu.se'),
    'CACHE_TIMEOUT': {
        'MANIFEST': 60 * 60 * 24,  # 24 hours
        'COLLECTION': 60 * 30,     # 30 minutes
    },
    'PROVIDER': {
        'id': 'https://www.gu.se/shfa',
        'name': {
            'en': 'SHFA - Rock Art Database',
            'sv': 'SHFA - Bilddatabas'
        },
        'homepage': 'https://shfa.dh.gu.se/about/en'
    }
}

# OAI-PMH Configuration (for future use)
OAI_CONFIG = {
    'REPOSITORY_NAME': 'SHFA Rock Art Database',
    'BASE_URL': getattr(settings, 'OAI_BASE_URL', 'https://shfa.dh.gu.se/api/shfa/OAICat/'),
    'ADMIN_EMAIL': getattr(settings, 'OAI_ADMIN_EMAIL', 'admin@shfa.dh.gu.se'),
    'COMPRESSION': ['gzip', 'deflate'],
    'DELETED_RECORD': 'persistent',
    'GRANULARITY': 'YYYY-MM-DD',
}