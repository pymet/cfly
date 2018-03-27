from cfly import build_module

mymodule = build_module(
    'mymodule',
    sources=['examples/sample_project/something.cpp'],
    preprocess=['examples/sample_project/module.cpp'],
)

print(mymodule.get_x())
