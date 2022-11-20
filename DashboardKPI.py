# In[]
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly
import numpy as np
import pandas as pd
import pymysql
import plotly.graph_objects as go
from cgitb import text

# %%
from dotenv import load_dotenv
import os

load_dotenv('.env')
# %%

print(os.getenv("HOST"))
host = os.getenv("HOST")
port = os.getenv("PORT")
user = os.getenv("USER")
password = os.getenv("PASSWORD")

# In[]
# try:
conn = pymysql.connect(host, port, user, passwd=password)
# except e:
# print(e)

# %%

# df = pd.read_sql_query("select month(odt) as Ordermonth,sub_status,count(distinct a.id) as TotalOrders, sum(case \
# when ost = 0 then 1 else 0 end) as Processing, sum(case when ost = 1 then 1 else 0 end) as Approved, \
# sum(case when ost = 2 then 1 else 0 end) as OnShipping,sum(case when ost = 3 then 1 else 0 end) as Shipped, \
# sum(case when ost = 4 then 1 else 0 end) as Complete, sum(case when ost = 5 then 1 else 0 end) as Canceled, \
# sum(case when ost = 6 then 1 else 0 end) as Returned \
# from rokomari_real.cust_order a  \
# where odt >= '2022-01-01' group by month(odt),sub_status", conn)

df = pd.read_sql_query("select month(odt) as Ordermonth,sub_status, count(distinct a.id) as TotalOrders, sum(case when a.ost = 0 then 1 else 0 end) as Processing, sum(case when a.ost = 1 then 1 else 0 end) as Approved, sum(case when a.ost = 2 then 1 else 0 end) as OnShipping,sum(case when a.ost = 3 then 1 else 0 end) as Shipped, sum(case when a.ost = 4 then 1 else 0 end) as Complete, sum(case when a.ost = 5 then 1 else 0 end) as Canceled, sum(case when a.ost = 6 then 1 else 0 end) as Returned ,sum(case when b.value in ('Customer ~ Duplicate Order','Customer ~ Merge Order', 'Customer ~ Test Order','Customer ~ Denied','Customer ~ Fake Order') then 1 else 0 end) as FakeCancels from rokomari_real.cust_order a left join rokomari_real.order_status_comment b on a.order_status_comment_id = b.id where odt >= '2022-01-01'  group by month (odt),sub_status", conn)

# %%

df = df.astype(dtype={'Processing': int, 'Approved': int, 'OnShipping': int,
                      'Shipped': int, 'Complete': int, 'Canceled': int, 'Returned': int, 'FakeCancels': int})

# %%
# --------------View By Sub Status---------
st.title('Overall View')
options = st.multiselect(
    'Search By Sub Status',
    # df['sub_status'].unique().tolist(),
    ['NORMAL', 'HALTED'],
    ['NORMAL']
)
# st.dataframe(df)
st.dataframe(df[df['sub_status'].isin(options)])


# %%
################## Summery By Deliveried##################
st.title('Deliered KPI-Placed to Delivered ')

df_delivered = pd.read_sql_query("select deliveryMonth, \
City,count(distinct ids) TotalDeliverd, \
sum(1stDay) as 1stDay,sum(2ndDay) as 2ndDay,sum(3rdDay) as 3rdDay, \
sum(4thDay) as 4thDay,sum(5thDay) as 5thDay,sum(moreThn5thDay) as moreThn5thDay \
from (select month(ddt) as deliveryMonth, \
case when b.ct_id = 2 then 'Dhaka' \
else 'Out Of Dhaka' end as City, a.id as ids,  \
case when timestampdiff(day,date(odt),date(ddt)) = 0 then 1 \
else 0 end as 1stDay, \
case when timestampdiff(day,date(odt),date(ddt)) = 1 then 1 \
else 0 end as 2ndDay, \
case when timestampdiff(day,date(odt),date(ddt)) = 2 then 1 \
else 0 end as 3rdDay, \
case when timestampdiff(day,date(odt),date(ddt)) = 3 then 1 \
else 0 end as 4thDay, \
case when timestampdiff(day,date(odt),date(ddt)) = 4 then 1 \
else 0 end as 5thDay, \
case when timestampdiff(day,date(odt),date(ddt)) > 4 then 1 \
else 0 end as moreThn5thDay \
from rokomari_real.cust_order a  \
left join rokomari_real.cust_order_shipping b on a.id = b.id \
where odt >= '2022-01-01' and year(ddt) > 2021 and ddt is not null \
) As total where deliveryMonth is not null \
group by deliveryMonth, City", conn)

df_delivered = df_delivered.astype(dtype={'1stDay': int, '2ndDay': int, '3rdDay': int,
                                          '4thDay': int, '5thDay': int, 'moreThn5thDay': int})


# %%
st.subheader("Orders Delivered in the months")
City = st.multiselect(
    'Filter By Dhaka Or Out of Dhaka',
    # df['sub_status'].unique().tolist(),
    ['Dhaka', 'Out Of Dhaka'],
    ['Dhaka']
)


if City != "":
    st.dataframe(df_delivered[df_delivered['City'].isin(City)])
    citywise = df_delivered[df_delivered['City'].isin(City)].groupby(
        ['deliveryMonth']).sum().reset_index()

elif City == "":
    st.dataframe(df_delivered[['deliveryMonth', 'TotalDeliverd', '1stDay', '2ndDay', '3rdDay']].groupby(
        ['deliveryMonth']).sum().reset_index())
    citywise = df_delivered[['deliveryMonth', 'TotalDeliverd', '1stDay', '2ndDay', '3rdDay']].groupby(
        ['deliveryMonth']).sum().reset_index()

# %%
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

fig = go.Figure()

fig.add_trace(go.Bar(
    x=months,
    y=(citywise['1stDay']/citywise['TotalDeliverd'])*100,
    name='1stDay',
    marker_color='goldenrod',
    text=citywise['1stDay'],
    textposition='auto'
))
fig.add_trace(go.Bar(
    x=months,
    y=(citywise['2ndDay']/citywise['TotalDeliverd'])*100,
    name='2ndDay',
    marker_color='lightsalmon',
    text=citywise['2ndDay'],
    textposition='auto'
))
fig.add_trace(go.Bar(
    x=months,
    y=(citywise['3rdDay']/citywise['TotalDeliverd'])*100,
    name='3rdDay',
    marker_color='lightcoral',
    text=citywise['3rdDay'],
    textposition='auto'
))

# Here we modify the tickangle of the xaxis, resulting in rotated labels.
fig.update_layout(barmode='stack', xaxis_tickangle=360, title='Day Wise Place To Delivery (% and Count)',
                  xaxis_title="Delivery Months", yaxis_title="Percentage (%)")

# fig.show()

st.write(fig)

# %%

#### Return Reason #########

reaturnReason = pd.read_sql_query(
    "select month(sdt) as sdtmonth,monthname(sdt) as shippedmonth,a.id,a.ost,b.value, if(a.id!=0,1,0) as retrnQty from rokomari_real.cust_order a left join rokomari_real.order_status_comment b on a.order_status_comment_id = b.id where sdt >= '2022-01-01' and odt >= '2022-01-01' and a.ost = 6", conn)

# monthwisereturn = reaturnReason[['returnedmonth', 'value', 'retrnQty']].groupby(
#     ['returnedmonth', 'value']).sum().reset_index()
rtnreasons = reaturnReason[['shippedmonth',
                            'id', 'value', 'retrnQty']].reset_index(drop=True)


# %%
# return Summery
st.subheader('Month Wise return')

totShipandReturn = pd.read_sql_query(
    "Select month(sdt) as month, count(distinct id) as totalShippedOrders,sum(case when ost = 6 then 1 else 0 end) as rtnqty from rokomari_real.cust_order a where sdt > '2022-01-01' group by month(sdt)", conn)
totShipandReturn = totShipandReturn.astype(dtype={'rtnqty': int})

totShipandReturn['% Of Return'] = (
    totShipandReturn['rtnqty']/totShipandReturn['totalShippedOrders'])*100


# %%
st.subheader("Return Order Qty By Shipped Month")

st.dataframe(totShipandReturn)

mn, rtn = st.columns(2)

mnth = mn.multiselect(
    label='Filter returned orderds By Shipped Month',
    options=rtnreasons['shippedmonth'].unique().tolist(),
    default=None, key='return'
)


if mnth == []:
    customdf = rtnreasons
    mn.dataframe(rtnreasons)
    nm = ['All Month']
elif mnth != "":
    customdf = rtnreasons[rtnreasons['shippedmonth'].isin(mnth)]
    nm = mnth
    mn.dataframe(customdf)


fig = px.pie(customdf, values='retrnQty', names='value',
             title='Retun Reason Percentages For ' + ', '.join(str(x) for x in nm))
fig.update_traces(textposition='inside', textinfo='percent+label')
# fig.show()

rtn.write(fig)

# %%
############# total cancel orders#########


totalcancel = pd.read_sql_query("select month(odt) as odtmonth,monthname(odt) as OrderedMonth,a.id,if(a.id != 0,1,0) as cancelQty ,b.value,case when b.value in ('Customer ~ Duplicate Order','Customer ~ Merge Order', 'Customer ~ Test Order','Customer ~ Denied','Customer ~ Fake Order') then 1 else 0 end as FakeCancels \
from rokomari_real.cust_order a \
left join rokomari_real.order_status_comment b on a.order_status_comment_id = b.id \
where odt >= '2022-01-01' and a.ost = 5 order by month(odt) asc", conn)

withoutFake = totalcancel[totalcancel['FakeCancels'] != 1]
withoutFake = withoutFake[['OrderedMonth', 'id', 'value', 'cancelQty']]


# %%

st.header('Cancel orders by order month')

effectiveCancels = df[['Ordermonth', 'TotalOrders', 'Canceled',
                       'FakeCancels']].groupby(['Ordermonth']).sum().reset_index()

effectiveCancels['effectiveorders'] = effectiveCancels['TotalOrders'] - \
    effectiveCancels['FakeCancels']

effectiveCancels['effectiveCancel'] = effectiveCancels['Canceled'] - \
    effectiveCancels['FakeCancels']


effectiveCancels['% effectiveCancel'] = (
    effectiveCancels.effectiveCancel/effectiveCancels.effectiveorders)*100

effectiveCancels = effectiveCancels[['Ordermonth',
                                     'effectiveorders', 'effectiveCancel', '% effectiveCancel']]

st.write('Effective Order is without Fake cancel orders from total orders')
st.dataframe(effectiveCancels)


# %%
# Pie Chart
cncl, Pie_cancel = st.columns(2)

# cncl.dataframe(withoutFake)

mnth_cancel = cncl.multiselect(
    label='Filter By Ordered Month',
    options=withoutFake['OrderedMonth'].unique().tolist(),
    default=None, key='cancel'
)


if mnth_cancel == []:
    customdfCancel = withoutFake
    cncl.dataframe(withoutFake)
    nm = ['All Month']
elif mnth_cancel != "":
    customdfCancel = withoutFake[withoutFake['OrderedMonth'].isin(mnth_cancel)]
    nm = mnth_cancel
    cncl.dataframe(customdfCancel)


fig = px.pie(customdfCancel, values='cancelQty', names='value',
             title='Cancel Reason Percentages For ' + ', '.join(str(x) for x in nm))
fig.update_traces(textposition='inside', textinfo='percent+label')


Pie_cancel.write(fig)
