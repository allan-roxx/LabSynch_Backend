"""
Standard pagination for all list endpoints.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """
    Standard paginator used across all LabSynch list endpoints.

    - Default page size: 20
    - Client can request up to 100 via ?page_size=N
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
