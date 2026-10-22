from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def register_view(request):
    if request.user.is_authenticated:
        return redirect("my_documents")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Your account has been created successfully.",
            )
            return redirect("my_documents")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("my_documents")

    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is not None:
                login(request, user)

                if url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

                return redirect("my_documents")
    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "accounts/login.html",
        {"form": form, "next": next_url},
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(
            request,
            "You have been logged out successfully.",
        )
        return redirect("login")

    return redirect("my_documents")
