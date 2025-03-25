from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Chat

# API credentials
awanllm_api_key = 'YOUR_API_KEY'
awanllm_url = 'https://api.awanllm.com/v1/chat/completions'

# Function to interact with the Awanllm API
def ask_awanllm(message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {awanllm_api_key}"
    }
    data = {
        "model": "Awanllm-Llama-3-8B-Cumulus",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }

    try:
        response = requests.post(awanllm_url, headers=headers, json=data)
        response.raise_for_status()  # Check for HTTP errors
        response_data = response.json()
        answer = response_data['choices'][0]['message']['content'].strip()
        return answer
    except requests.RequestException as e:
        # Handle request errors
        return f"Error contacting the assistant: {e}"

# Chatbot view for handling user messages
@login_required(login_url='login')
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            response = ask_awanllm(message)

            chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
            chat.save()
            return JsonResponse({'message': message, 'response': response})
        else:
            return JsonResponse({'error': 'Message content is required.'}, status=400)

    return render(request, 'chatbot.html', {'chats': chats})

# Login view for user authentication
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(request, username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

# Registration view for creating new users
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                error_message = 'Username already exists'
            elif User.objects.filter(email=email).exists():
                error_message = 'Email already registered'
            else:
                try:
                    user = User.objects.create_user(username=username, email=email, password=password1)
                    user.save()
                    auth.login(request, user)
                    return redirect('chatbot')
                except Exception as e:
                    error_message = f"Error creating account: {e}"
            return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = "Passwords don't match"
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

# Logout view for logging out the user
def logout(request):
    auth.logout(request)
    return redirect('login')
