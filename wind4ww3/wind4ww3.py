#!/home/anahon/anaconda3/envs/py36/bin/python3
# -*- coding: utf-8 -*-

###
# A.Nahon - anahon@lnec.pt - May 2020
# adapted from A.Azevedo joinSflux.py:
#   - It maintains the code original functions and structure to merge
#   netcdf files from the era5 repository;
#   - It was incremented with the time_to_julian function which handles
#   the conversion need for archive with a different time reference;
#   - Options for cfsr and gfs were added.
###

import os
import sys
import numpy as np
from glob import glob
from pathlib import Path
import netCDF4 as netcdf4
from datetime import datetime, date


def time_to_julian(time, date_zero):
    delta = date(date_zero[0], date_zero[1], date_zero[2]) - date(1900, 1, 1)
    julian_time = time + delta.days
    julian_zero = np.array([1900, 1, 1, 0])
    return julian_time, julian_zero


def write_sflux_ww3(file='sflux_air_1.ww3.nc',
                    idate=np.array([1900, 1, 1, 0]), t=np.array([]),
                    latt=np.array([]), long=np.array([]),
                    u=np.array([]), v=np.array([]), **ncvar_kwargs):
    if idate[0]!=1900:
        print('changing dates')
        t, idate = time_to_julian(t, idate)
    f = netcdf4.Dataset(file, 'w')
    f.Conventions = 'CF-1.0'
    f.createDimension('time', len(t))
    f.createDimension('lon', long.shape[1])
    f.createDimension('lat', latt.shape[0])

    # Time
    time = f.createVariable('time', np.float64, ('time',))
    time[:] = t
    time.long_name = 'Time'
    time.standard_name = 'time'
    dateIni = datetime(idate[0], idate[1], idate[2], idate[3])
    time.units = dateIni.strftime("days since %Y-%m-%d %H:%M:%S")
    time.base_date = idate
    time.calendar = 'julian'

    # Longitude
    lon = f.createVariable('lon', 'f', ('lat', 'lon'), **ncvar_kwargs)
    lon[:, :] = long
    lon.long_name = 'Longitude'
    lon.standard_name = 'longitude'
    lon.units = 'degrees_east'

    # Latitude
    lat = f.createVariable('lat', 'f', ('lat', 'lon'), **ncvar_kwargs)
    lat[:, :] = latt
    lat.long_name = 'Latitude'
    lat.standard_name = 'latitude'
    lat.units = 'degrees_north'

    # Uwind
    uwind = f.createVariable('uwind', 'f', ('time', 'lat', 'lon'), **ncvar_kwargs)
    uwind[:, :, :] = u
    uwind.long_name = 'Surface Eastward Air Velocity (10m AGL)'
    uwind.standard_name = 'eastward_wind'
    uwind.units = 'm/s'

    # Vwind
    vwind = f.createVariable('vwind', 'f', ('time', 'lat', 'lon'), **ncvar_kwargs)
    vwind[:, :, :] = v
    vwind.long_name = 'Surface Northward Air Velocity (10m AGL)'
    vwind.standard_name = 'northward_wind'
    vwind.units = 'm/s'

    f.close()
    print("\n" + file + " saved !!!")
    return None


if __name__ == '__main__':
    try:
        archive_source = sys.argv[1]
        print(f'Converting wind data from {archive_source} archive')
    except ValueError as err:
        print('!!! ', err)
        print('Please specify the archive source: ')
        print('either era5, cfsr or gfs')
        exit()

    cwd = Path()
    files = sorted(glob("/".join([str(cwd), "*.nc"])))

    sfluxDict = {}
    for n, file in enumerate(files):
        nc = netcdf4.Dataset(file)
        if archive_source == 'era5':
            time = nc.variables["time"]
            if n == 0:
                idate = np.array([int(i) for i in "-".join([time.units.split()[-1], "0"]).split("-")])
                lat = nc.variables["lat"][:]
                lon = nc.variables["lon"][:]
            u = nc.variables["uwind"][:]
            v = nc.variables["vwind"][:]

        elif archive_source == 'cfsr':
            t_ref = np.datetime64('1900-01-01T00:00:00')
            valid_date_str = ["".join(nc.variables['valid_date_time'][i].astype(str).tolist()) for i in
                              range(len(nc.variables['valid_date_time']))]
            valid_date_time = np.array([datetime.strptime(d, '%Y%m%d%H') for d in valid_date_str],
                                       dtype='datetime64[s]')
            valid_date_dt = valid_date_time - t_ref
            time = valid_date_dt.astype(float) / 24 / 60 / 60
            print(time[0])
            if n == 0:
                idate = np.array([1900, 1, 1, 0])
                lat_vec = nc.variables["lat"][:]
                lon_vec = nc.variables["lon"][:]
            u = nc.variables["U_GRD_L103"][:]
            v = nc.variables["V_GRD_L103"][:]
            lon = lon_vec
            lat = lat_vec
            for i in range(len(lat_vec) - 1):
                lon = np.append(lon, lon_vec)
            lon = np.reshape(lon, (len(lat_vec), len(lon_vec)))
            for i in range(len(lon_vec) - 1):
                lat = np.append(lat, lat_vec)
            lat = np.reshape(lat, (len(lon_vec), len(lat_vec)))
            lat = np.transpose(lat)

        elif archive_source == 'gfs':
            time = nc.variables["time"]
            time = np.divide(time, 24 * 60 * 60)
            if n == 0:
                idate = np.array([1970, 1, 1, 0])
                lat_vec = nc.variables["latitude"][:]
                lon_vec = nc.variables["longitude"][:]
            u = nc.variables["UGRD_10maboveground"][:]
            v = nc.variables["VGRD_10maboveground"][:]
            lon = lon_vec
            lat = lat_vec
            for i in range(len(lat_vec) - 1):
                lon = np.append(lon, lon_vec)
            lon = np.reshape(lon, (len(lat_vec), len(lon_vec)))
            for i in range(len(lon_vec) - 1):
                lat = np.append(lat, lat_vec)
            lat = np.reshape(lat, (len(lon_vec), len(lat_vec)))
            lat = np.transpose(lat)
        else:
            print('Archive source is not defined properly!')
            print('Please define it as either era5, cfsr or gfs')
            exit()

        f = file.split("/")[-1]
        sfluxDict[f] = {"filename": f, "idate": idate, "time": time[:], "u": u, "v": v}

        if n == 0:
            tTotal = sfluxDict[files[n].split("/")[-1]]["time"]
        else:
            tTotal = np.hstack((tTotal, sfluxDict[files[n].split("/")[-1]]["time"]))

        if n == 0:
            uTotal = sfluxDict[files[n].split("/")[-1]]["u"]
        else:
            uTotal = np.vstack((uTotal, sfluxDict[files[n].split("/")[-1]]["u"]))

        if n == 0:
            vTotal = sfluxDict[files[n].split("/")[-1]]["v"]
        else:
            vTotal = np.vstack((vTotal, sfluxDict[files[n].split("/")[-1]]["v"]))

    fout = "sflux_air.ww3.nc"
    if os.path.exists(fout):
        os.remove(fout)
    write_sflux_ww3(file=fout, idate=idate, t=tTotal, latt=lat, long=lon, u=uTotal, v=vTotal)
