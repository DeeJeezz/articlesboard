from channels.routing import ProtocolTypeRouter, URLRouter
# import articles.routing
# from channels import route
# from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    # 'websocket': AuthMiddlewareStack(
    #     URLRouter(
    #         articles.routing.websocket_urlpatterns
    #     )
    # ),
})