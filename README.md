# Steps to run Heat2D MASS simulation:
```
1. make develop LLVM_PREBUILD_DOWNLOAD_URL=https://github.com/llvm/llvm-project/releases/download/llvmorg-14.0.6/clang+llvm-14.0.6-x86_64-linux-gnu-rhel-8.4.tar.xz

2. make build

3. ./bin/Heat2D_PlaceV2
```

Using the ```--help``` flag will print different flags that can be used to define simulation parameters.
You must use the ```--verbose``` flag to see the square. For example, a line I am using to debug the application is:
```
./bin/Heat2D_PlaceV2 --interval 1 --verbose 
```

Max size as of MASS v0.7.2, this implementation as of 5/10/2024, is 3083.
4. make build-simviz 
5. ./bin/simviz heat2d.viz 

sh run.sh 
./run.sh 


You may need to install plotly. 
run this command: 

python3 -m pip install 
plotly 

python3 -m pip install --user plotly


And then : 
python3 visualize_plotly.py