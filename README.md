# solidpython_ff


Fast and Furious [solidpython](https://github.com/SolidCode/SolidPython), more pythonic!

[Solidpython](https://github.com/SolidCode/SolidPython)sticks to [Openscad's](https://www.openscad.org/) operation(arguments) (objects,...) API.

This is a slim wrapper (and some tiny utility functions) that turn this into a
python object.operation(arguments) API. 

For example:

```
translate([0,0,10]) ( 
	cylinder(r=3,h=10) + 
	rotate([0,90,0]) ( 
		cylinder(r=3, h=10 )
		)
)
```

becomes 
```
(cylinder(r=3, h=10) + cylinder(r=3, h=10).rotate([0,90,0])).translate([0,0,10])
```

There's also abbreviations, so you can go 

```
cy(r=3, h=10) + cy(r=3, h=10).r([0,90,0])).t([0,0,10])
```

The functions have been tuned to understand to understand
the openscady 'list-triplets' as well as regular old parameters, 
and the utils convenience functions are also available.

```
cy(r=3, h=10) + cy(r=3, h=10).r(0,90,0)).t(0,0,10)
```

Or even 
```
(cy(r=3, h=10) + cy(r=3, h=10)).rzx().up(10) # rotate z to x
```


More convenience:

```
cy(r=3, h=10, segments = 64).scale(x=10, y=5) # z = 1 is implied, 64 segments is the default
cy(r=3, h=10).s(x=10, y=5) # z = 1 is implied

square(3,5).e(10, axis='x', center=True) #  a rectangle 3*5, extruded by 10mm, down 5mm, rotated so that extrusion direction is in the x axis.


cy(3,0).debug() # translates to # in openscad
cy(3,0).d()

cy(3,0).background() # translates to % in openscad
cy(3,0).b()


q(10,20,30) + cy(1.5,31).hole() # or .h() for 'first class negative space, and quick cubes

rq(10, r=2, axis='x', edges=(0,1)) # a 10x10x10 cube that has the top edges, parallel to the x axis rounded (so the 'straight' face is facing x)


q(10).x(5) # alias for forward. 
q(10).y(5) # alias for right. 
q(10).z(5) # alias for up. 


q(10).dump("example.scad") # write the object to a .scad file (calls scad_render_to_file)



```



