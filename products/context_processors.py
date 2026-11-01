from .services import favorite_price_drops


def favorite_drop_count(request):
    """Number of favorites that got cheaper, shown next to "Favoritos" in the header."""
    if not request.user.is_authenticated:
        return {}
    return {'favorite_drop_count': len(favorite_price_drops(request.user))}
