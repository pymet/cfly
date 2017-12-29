from cfly import load_folder

module = load_folder('examples/load_folder_example')
hello = module.get('hello')
hello()
