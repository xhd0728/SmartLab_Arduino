from django.shortcuts import render, redirect
from rest_framework.views import APIView
from .models import User


class LoginView(APIView):
    """
    登录控制
    """

    def get(self, request):
        """
        html页面渲染
        :param request: 请求体
        :return: HTTPResponse
        """
        return render(request, "login.html")

    def post(self, request):
        """
        登录校验
        :param request: 请求体
        :return: HTTPResponseRedirect
        """
        username = request.data.get("username")
        password = request.data.get("password")
        if not User.objects.filter(username=username).count():
            return redirect("/login")
        user = User.objects.get(username=username)
        if user.password != password:
            return redirect("/login")
        return redirect("/dashboard")


class DashboardView(APIView):
    def get(self, request):
        return render(request, "dashboard.html")
