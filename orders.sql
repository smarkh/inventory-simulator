select Item_Number as sku, sum(Quantity) as qty
from blend..spvSalesLineItemSearch
where (Sales_Doc_Num like 'WEB%'
	or Sales_Doc_Num like 'Owa%')
	and Sales_Doc_Type = 'order'
	and Item_Number not like 'TX-%'
	and source = 'history'
	and Doc_Date >= '2021-03-01'
	and Item_Description not like '%component%'
	and Item_Description not like '%COTM%'
	and Item_Description not like '%COTS%'
	and Item_Description not like 'swag%'
	and Item_Description not like '%replacement%'
	and Item_Description not like '%assortment%'
	and Doc_Date >= DATEADD(week, -6, GETDATE())


select ITEMNMBR as sku, QTYONHND as on_hand, ATYALLOC as alloc 
from blend..iv00102
where LOCNCODE = '3PL East'
	and QTYONHND - ATYALLOC > 0
