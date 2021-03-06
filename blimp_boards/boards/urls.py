from django.conf.urls import patterns, url

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()

router.register(r'boards/collaborators/requests',
                views.BoardCollaboratorRequestViewSet)
router.register(r'boards/collaborators', views.BoardCollaboratorViewSet)
router.register(r'boards', views.BoardViewSet)

api_urlpatterns = router.urls


urlpatterns = patterns(
    # Prefix
    '',

    url(r'^$', views.BoardHTMLView.as_view(), name='board_detail')
)
