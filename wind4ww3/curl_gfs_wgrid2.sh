# requires wgrid2.exe
# (https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/index.html)
# tested with v3.0.2 built for windows
 
rm temp*file *.nc
rm *.grb2 *.tar
rm file_list
curl --output file_list --list-only $1

# note that the list of files in file_list may not be in the expected
# chronological order. This should be changed

counter=0
while read f
do
	(( counter++ ))
	echo $counter
	echo $1$f
	file_to_download="curl -O $1$f"
	eval ${file_to_download}
	tar_archive="tar -xvf $f"
	eval ${tar_archive}
	rm *.tar
	rm temp_1_file
	for g in *.grb2
	do
		echo $g
		../wgrid2/v3.0.2/wgrib2.exe $g -match '(:(UGRD|VGRD):10 m above ground:|:PRMSL:mean sea level:|:TMP:surface:)' -match ':(anl|(3|6|9|12|15|18|21) hour fcst):' -append -new_grid_winds earth -new_grid latlon -98:223:0.5 0:151:0.5 temp_1_file
	done
	../wgrid2/v3.0.2/wgrib2.exe temp_1_file -append -new_grid_winds earth -new_grid latlon -98:223:0.5 0:151:0.5 temp_2_file
	rm *.grb2
done <./file_list
../wgrid2/v3.0.2/wgrib2.exe temp_2_file -netcdf file.nc