import datetime
import os
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import requests
import json

from carts.models import CartItem
from orders.forms import OrderForm
from orders.models import Order, OrderProduct, Payment
from store.models import Product

# Create your views here.

# ================================================PAYMENT INITIATION==================================================================================

def payments(request):
    url = "https://a.khalti.com/api/v2/epayment/initiate/"

    if request.method == 'POST':
        return_url = request.POST.get('return_url')
        website_url = request.POST.get('return_url')
        purchase_order_id = request.POST.get('purchase_order_id')
        amount = float(request.POST.get('amount'))
        user = request.user

        #Change the amount into integer

        amount_int = int(float(amount))

        print("url",url)
        print("return_url",return_url)
        print("web_url",website_url)
        print("amount",amount)
        print("purchase_order_id",purchase_order_id)

       
        

        payload = json.dumps({
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount_int,
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
        print(type(new_res))
        return redirect(new_res['payment_url'])
    return redirect('accounts')

# ===================================================VERIFY PAYMENT======================================================================================

def verify_payment(request):

    url = "https://a.khalti.com/api/v2/epayment/lookup/"
    if request.method == 'GET':
        headers = {
            'Authorization': 'key f58207f6173d4159b46014b8009889b6',
            'Content-Type': 'application/json',
        }
        pidx = request.GET.get('pidx')
        data = json.dumps({
            'pidx': pidx
        })
        res = requests.request('POST', url, headers=headers, data=data)
        print(res)
        print(res.text)
        new_res = json.loads(res.text)
        print(new_res)

        if new_res['status'] == 'Completed':
            # # Fetch order by purchase_order_id
            # purchase_order_id = new_res['purchase_order_id']
            # if not purchase_order_id:
            #     return redirect('payment_failed')
            # order = get_object_or_404(Order, order_number=purchase_order_id)

            order_number = request.GET.get('purchase_order_id')
            amount = new_res.get('total_amount', 0)

            order = get_object_or_404(Order, order_number=order_number)
            
            # Create a payment record
            payment = Payment(
                user=order.user,
                payment_id=pidx,
                payment_method='Khalti',
                amount_paid=amount,
                status=new_res['status']
            )
            payment.save()
            
            # Update order status
            order.is_ordered = True
            order.payment = payment
            order.save()

            # # Move cart items to order products
            # cart_items = CartItem.objects.filter(user=order.user)
            # for item in cart_items:
            #     order_product = OrderProduct()
            #     order_product.order_id = order.id
            #     order_product.payment = payment
            #     order_product.user_id = order.user.id
            #     order_product.product_id = item.product_id
            #     order_product.quantity = item.quantity
            #     order_product.product_price = item.product.price
            #     order_product.ordered = True
            #     order_product.save()

            #     # Reduce the quantity of the sold products
            #     product = Product.objects.get(id=item.product_id)
            #     product.stock -= item.quantity
            #     product.save()

            # # Clear the cart
            # CartItem.objects.filter(user=order.user).delete()

            
        else:
            pass

    return redirect('accounts')



#======================================================= PLACE ORDER==========================================================================

def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart count is less than or equal to zero, redirect to store page
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing info inside the order table
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
            # Generate Order Number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")  # 2021/4/6
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')