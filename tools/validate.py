import sys, itertools; sys.path.insert(0,'tools')
import proj as P
from shapely.ops import unary_union
eq=P.ekipman_poligonlari()
bad=0
for a,b in itertools.combinations(eq,2):
    i=a[2].intersection(b[2]).area
    if i>1e-6: print("ÇAKIŞMA",a[0],b[0],round(i,3)); bad+=1
for k,ad,g in eq:
    d=g.difference(P.SALON).area
    if d>1e-6: print("DIŞARI",k,round(d,3)); bad+=1
    print(f"  {k:3s} duvara {g.distance(P.SALON.exterior):.2f} m")
free=P.SALON.difference(unary_union([g for _,_,g in eq]).buffer(0.001))
print("serbest sirkülasyon alanı:", round(free.area,2), "m²  (salon", P.A['salon'],")")
print("ekipman kapladığı:", round(P.EK_ALAN,2), "m²")
print("SONUÇ:", "TEMİZ" if bad==0 else f"{bad} sorun")
