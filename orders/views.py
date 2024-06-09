import datetime
import uuid
from django.http import HttpResponse
from django.shortcuts import redirect, render
import requests

import json

from carts.models import CartItem
from orders.forms import OrderForm
from orders.models import Order


# Create your views here.

def payments(request):
    url = "https://a.khalti.com/api/v2/epayment/initiate/"

    return_url = request.POST.get('return_url')
    purchase_order_id = request.POST.get('purchase_order_id')
    amount = request.POST.get('amount')

    print("return_url", return_url)
    print("amount", amount)
    print("purchase_order_id", purchase_order_id)
    user = request.user

    payload = json.dumps({
        "return_url": return_url,
        "website_url":"http://127.0.0.1:8000",
        "amount": amount,
        "purchase_order_id": purchase_order_id,
        "purchase_order_name": "test",
        "customer_info": {
        "name": user.first_name,
        "email": user.email,
        "phone": user.phone_number
        }
    })
    headers = {
        'Authorization': 'key f58207f6173d4159b46014b8009889b6',
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    new_res = json.loads(response.text)
    print(new_res)
    # return render(request, 'orders/payments.html')
    return redirect(new_res['payment_url'])

    


def verify_payment(request):

    url = "https://a.khalti.com/api/v2/epayment/lookup/"

    pidx = request.GET.get('pidx')

    headers = {
        'Authorization': 'key f58207f6173d4159b46014b8009889b6',
        'Content-Type': 'application/json',
    }

    payload = json.dumps({
        'pidx': pidx
    })

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    new_res = json.loads(response.text)
    print(new_res)
   
    return redirect("place_order")




def place_order(request, total= 0, quantity=0):
    current_user = request.user

    #if the cart count is less than or equal to zero, redirect to store page

    cart_items = CartItem.objects.filter(user= current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    

    
    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total)/100
    grand_total = total + tax

    if request.method =='POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            #store all the billing info inside order table.
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            #Generate Order Number

            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d") #2021/4/6
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user= current_user, is_ordered=False, order_number=order_number)

            # Generate the purchase order ID
            purchase_order_id = generate_purchase_order_id('khalti')

            context={

                'order' : order,
                'cart_items' : cart_items,
                'total' : total,
                'tax' : tax,
                'grand_total' : grand_total,
                'purchase_order_id': purchase_order_id,
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')
    

def generate_purchase_order_id(integration_name):
    # Generate a unique UUID (Universally Unique Identifier)
    uuid_part = str(uuid.uuid4())[:8]  # Take the first 8 characters of the UUID

    # Get the current date and time
    now = datetime.datetime.now()

    # Format the date and time as a string (YYYYMMDDHHMMSS)
    date_part = now.strftime("%Y%m%d%H%M%S")

    # Include the integration name in the purchase order ID
    integration_part = integration_name[:3].upper()  # Take the first 3 characters of the integration name and convert to uppercase

    # Combine the UUID part, date part, and integration part to create the purchase order ID
    purchase_order_id = f"{date_part}-{integration_part}-{uuid_part}"

    return purchase_order_id

