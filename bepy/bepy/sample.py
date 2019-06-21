import pandas as pd
import numpy as np
from bepy import LineMeasurement, GridMeasurement
import os


class Sample:

    @property
    def linemeasurements(self):
        return

    @property
    def gridmeasurements(self):
        return

    # Store flags identifying bad acquisitions
    @property
    def meas_acq_flags(self):
        return

    def __init__(self, path=None, gridSize=50, adjustphase=True):

        self._linemeasurements = {}
        self._gridmeasurements = {}
        self._meas_acq_flags = {}

        if path is not None:
            self.addentiresample(path, gridSize, adjustphase)

    def addmeasurement(self, meas, measType=None, measName=None, gridSize=None, adjustphase=True):

        if measType is None:
            measType = meas._measurementName
            meas_flags = meas.clean()

            if measType == 'Scan':
                self._linemeasurements[measType] = meas
            elif measType in ['SSPFM', 'NonLin', 'Relax']:
                self._gridmeasurements[measType] = meas
            else:
                raise ValueError(measType+': Unknown measurement type')

        else:
            if measType.lower() in 'scan':
                try:
                    newMeas = LineMeasurement(meas, name=measName, adjustphase=adjustphase)
                except ValueError:
                    raise ValueError('Argument is not a path to measurement data. Maybe its a Measurement Object?')
                meas_flags = newMeas.clean()
                self._linemeasurements[measName] = newMeas
            else:
                if measType.lower() in ['grid']:
                    measType = 'Relax'
                try:
                    newMeas = GridMeasurement(meas, measType, gridSize, adjustphase=adjustphase)
                except ValueError:
                    raise ValueError('Argument is not a path to measurement data. Maybe its a Measurement Object?')
                meas_flags = newMeas.clean()
                self._gridmeasurements[measName] = newMeas

        self._meas_acq_flags[measType] = meas_flags

    def addentiresample(self, path, gridSize=50, adjustphase=True):

        directory_list = list()
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                directory_list.append(os.path.join(root, name))

        for directory in directory_list:

            if os.path.isfile(directory+'/shofit.csv'):
                parameters = pd.read_csv(directory + '/parameters.csv', header=None, index_col=0)

                try:
                    measType = parameters.T['Measurement Type'].values[0]
                    measName = parameters.T['Measurement Name'].values[0]
                except KeyError:
                    measType = 'Grid'
                    measName = 'Fail'

            self.addmeasurement(directory+'/', measType=measType, measName=measName, gridSize=gridSize, adjustphase=adjustphase)

    def GetMeasStack(self, measstack = None, varstack = ['Amp', 'Phase', 'Res', 'Q'], inout=0.0, plotGroup=None,
                     insert=None, clean=False):

        if measstack is None:
            measstack = self._gridmeasurements.keys()

        stackedCols = 0
        stackreturn = 0

        flags = []

        for measure in measstack:

            measurement = self._gridmeasurements[measure]
            meas_flags = self._meas_acq_flags[measure]
            data = measurement.GetDataSubset(inout=inout, plotGroup=plotGroup, insert=insert,
                                             stack=varstack)

            cols = data.columns.values
            unzipped = np.asarray([list(t) for t in zip(*cols)])
            measname = np.repeat(measure, unzipped.shape[1])
            newcols = np.vstack([measname, unzipped])

            try:
                stackreturn = pd.concat([stackreturn, data], axis=1)
                stackedCols = np.hstack([stackedCols, newcols])
                flags = np.hstack([flags, meas_flags])
            except TypeError:
                stackreturn = data
                stackedCols = newcols
                flags = meas_flags
                
        tuples = list(zip(*stackedCols))

        cols = pd.MultiIndex.from_tuples(tuples, names=['Meas', 'Var', 'Chirp', 'InOut', 'PlotGroup', 'xaxis'])

        result = pd.DataFrame(stackreturn.values, index=stackreturn.index, columns=cols)

        if clean:
            try:
                collapsed_flags = flags.any(axis=1)
            except:
                collapsed_flags = flags

            result =  result[~collapsed_flags]
            return result, collapsed_flags
        else:
            return result

    def plot(self, meas=None, variables=None, saveName=None, pointNum=None, InOut=0):

        if meas == 'Scan':
            try:
                measObj = self._linemeasurements[meas]
            except KeyError:
                raise KeyError('That measurement does not exist')
            measObj.plot(variables=variables, saveName=saveName)
        elif meas in ['SSPFM', 'NonLin', 'Relax']:
            try:
                measObj = self._gridmeasurements[meas]
            except KeyError:
                raise KeyError('That measurement does not exist')
            measObj.plot(variables=variables, pointNum=pointNum, InOut=InOut, saveName=saveName)
        else:
            raise ValueError('Please select which measurement to plot')