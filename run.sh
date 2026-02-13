chmod +x bin/Heat2D_PlaceV2 
./bin/Heat2D_PlaceV2 --interval 1 --verbose   > log.txt  
echo "Parsing log.txt to structured data..."          
python3 parse_heat2d.py      
python3 visualize_ploty.py                                          