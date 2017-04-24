# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nose import with_setup

import os
import shutil
import ftplib
import numpy
import spectral
import pycoal
from pycoal import mineral
from pycoal import mining

# file names of USGS Digital Spectral Library 06 in ENVI format
libraryFilenames = ["s06av95a_envi.hdr", "s06av95a_envi.sli"]

# set up test module before running tests
def setup_module(module):

    # enter test directory
    os.chdir('pycoal/tests')

    # download spectral library over FTP if necessary
    if not os.path.isfile(libraryFilenames[0]) and \
       not os.path.isfile(libraryFilenames[1]):
        ftp_url = "ftpext.cr.usgs.gov"
        ftp_dir = "pub/cr/co/denver/speclab/pub/spectral.library/splib06.library/Convolved.libraries/"
        ftp = ftplib.FTP(ftp_url)
        ftp.login()
        ftp.cwd(ftp_dir)
        for f in libraryFilenames:
            with open("" + f, "wb") as lib_f:
                ftp.retrbinary('RETR %s' % f, lib_f.write)

# tear down test module after running tests
def teardown_module(module):

    # leave test directory
    os.chdir('../..')

# test files for classifyImage tests
# TODO test AVIRIS-C
test_classifyImage_testFilenames = ["ang20140912t192359_corr_v1c_img_400-410_10-20.hdr",
                                    "ang20140912t192359_corr_v1c_img_2580-2590_540-550.hdr",
                                    "ang20150422t163638_corr_v1e_img_4000-4010_550-560.hdr"]

# delete temporary files for classifyImage tests
def _test_classifyImage_teardown():
    for filename in test_classifyImage_testFilenames:
        try:
            os.remove(filename[:-4] + "_class_test.hdr")
            os.remove(filename[:-4] + "_class_test.img")
        except OSError:
            pass

# verify that classified images have valid classifications
@with_setup(None, _test_classifyImage_teardown)
def test_classifyImage():

    # create mineral classifier instance
    mc = mineral.MineralClassification(libraryFilenames[0])

    # make sure library is opened correctly
    assert isinstance(mc.library, spectral.io.envi.SpectralLibrary)

    # for each of the test images
    for imageFilename in test_classifyImage_testFilenames:

        # classify the test image
        classifiedFilename = imageFilename[:-4] + "_class_test.hdr"
        mc.classifyImage(imageFilename, classifiedFilename)
        actual = spectral.open_image(classifiedFilename)

        # classified image for comparison
        expected = spectral.open_image(imageFilename[:-4] + "_class.hdr")

        # validate metadata
        assert expected.metadata.get(u'description') == 'PyCOAL '+pycoal.version+' mineral classified image.'
        assert expected.metadata.get(u'file type') == actual.metadata.get(u'file type')
        assert expected.metadata.get(u'map info') == actual.metadata.get(u'map info')
        assert expected.metadata.get(u'class names') == actual.metadata.get(u'class names')
        assert expected.metadata.get(u'classes') == actual.metadata.get(u'classes')

        # verify that every pixel has the same classification
        assert numpy.array_equal(expected.asarray(), actual.asarray())

# test files for classify image threshold and subset tests
test_classifyImage_threshold_subset_imageFilename = 'ang20150420t182808_corr_v1e_img_4200-4210_70-80.hdr'
test_classifyImage_threshold_subset_testFilename = 'ang20150420t182808_corr_v1e_img_4200-4210_70-80_class_test.hdr'
test_classifyImage_threshold_subset_testImage = 'ang20150420t182808_corr_v1e_img_4200-4210_70-80_class_test.img'
test_classifyImage_threshold_subset_classifiedFilename = 'ang20150420t182808_corr_v1e_img_class_4200-4210_70-80.hdr'

# tear down classify image subset test by deleting classified file
def _test_classifyImage_threshold_subset_teardown():
    try:
        os.remove(test_classifyImage_threshold_subset_testFilename)
        os.remove(test_classifyImage_threshold_subset_testImage)
    except OSError:
        pass

# verify that threshold classification gives either the same result or no data for each pixel
@with_setup(None, _test_classifyImage_threshold_subset_teardown)
def test_classifyImage_threshold():

    # create mineral classification instance with threshold
    mc = mineral.MineralClassification(libraryFilenames[0], threshold=0.75)

    # classify image
    mc.classifyImage(test_classifyImage_threshold_subset_imageFilename, \
                     test_classifyImage_threshold_subset_testFilename)
    actual = spectral.open_image(test_classifyImage_threshold_subset_testFilename)

    # compare expected to actual classifications
    expected = spectral.open_image(test_classifyImage_threshold_subset_classifiedFilename)
    for x in range(actual.shape[0]):
        for y in range(actual.shape[1]):
            actualClassId = actual[x,y,0]
            actualClassName = actual.metadata.get('class names')[actualClassId]
            expectedClassId = expected[x,y,0]
            expectedClassName = expected.metadata.get('class names')[expectedClassId]
            assert actualClassName == expectedClassName \
                or actualClassName == 'No data'

# verify that subset classification identifies only the selected classes
@with_setup(None, _test_classifyImage_threshold_subset_teardown)
def test_classifyImage_subset():

    # create mineral classification instance with mining subset
    mc = mineral.MineralClassification(libraryFilenames[0], classNames=mining.proxyClassNames)

    # classify image
    mc.classifyImage(test_classifyImage_threshold_subset_imageFilename, \
                     test_classifyImage_threshold_subset_testFilename)
    actual = spectral.open_image(test_classifyImage_threshold_subset_testFilename)

    # inspect the classifications
    for x in range(actual.shape[0]):
        for y in range(actual.shape[1]):
            actualClassId = actual[x,y,0]
            actualClassName = actual.metadata.get('class names')[actualClassId]
            assert actualClassName in mining.proxyClassNames \
                or actualClassName == 'No data'

# test files for filterClasses test
test_filterClasses_Filename = 'ang20150420t182808_corr_v1e_img_class_4200-4210_70-80.hdr'
test_filterClasses_Image = 'ang20150420t182808_corr_v1e_img_class_4200-4210_70-80.img'
test_filterClasses_testFilename = 'ang20150420t182808_corr_v1e_img_class_4200-4210_70-80_filtered.hdr'
test_filterClasses_testImage = 'ang20150420t182808_corr_v1e_img_class_4200-4210_70-80_filtered.img'

# set up filterClasses test by copying classified image
def _test_filterClasses_setup():
    shutil.copyfile(test_filterClasses_Filename, test_filterClasses_testFilename)
    shutil.copyfile(test_filterClasses_Image, test_filterClasses_testImage)

# tear down filterClasses test by deleting filtered image
def _test_filterClasses_teardown():
    try:
        os.remove(test_filterClasses_testFilename)
        os.remove(test_filterClasses_testImage)
    except OSError:
        pass

# verify that filterClasses removes unused classes and reindexes correctly
@with_setup(_test_filterClasses_setup, _test_filterClasses_teardown)
def test_filterClasses():
    mineral.MineralClassification.filterClasses(test_filterClasses_testFilename)
    original = spectral.open_image(test_filterClasses_Filename)
    filtered = spectral.open_image(test_filterClasses_testFilename)
    assert int(filtered.metadata.get('classes')) == len(set(original.asarray().flatten().tolist()))
    for x in range(original.shape[0]):
        for y in range(original.shape[1]):
            originalClassName = original.metadata.get('class names')[original[x,y,0]]
            filteredClassName = filtered.metadata.get('class names')[filtered[x,y,0]]
            assert originalClassName == filteredClassName

# test files for AVIRIS-NG toRGB test
test_toRGB_imageFilename = 'ang20150422t163638_corr_v1e_img_987_654.hdr'
test_toRGB_rgbFilename = 'ang20150422t163638_corr_v1e_img_987_654_rgb.hdr'
test_toRGB_testFilename = 'ang20150422t163638_corr_v1e_img_987_654_rgb_test.hdr'
test_toRGB_testImage = 'ang20150422t163638_corr_v1e_img_987_654_rgb_test.img'

# tear down AVIRIS-NG toRGB test by deleting temporary files
def _test_toRGB_teardown():
    try:
        os.remove(test_toRGB_testFilename)
        os.remove(test_toRGB_testImage)
    except OSError:
        pass

# verify that the RGB converter selects the correct AVIRIS-NG bands and updates the metadata
@with_setup(None, _test_toRGB_teardown)
def test_toRGB():
    mineral.MineralClassification.toRGB(test_toRGB_imageFilename, test_toRGB_testFilename)
    expected = spectral.open_image(test_toRGB_rgbFilename)
    actual = spectral.open_image(test_toRGB_testFilename)
    assert numpy.array_equal(expected.asarray(), actual.asarray())
    assert expected.metadata.get('wavelength') == actual.metadata.get('wavelength')
    assert expected.metadata.get('correction factors') == actual.metadata.get('correction factors')
    assert expected.metadata.get('fwhm') == actual.metadata.get('fwhm')
    assert expected.metadata.get('bbl') == actual.metadata.get('bbl')
    assert expected.metadata.get('smoothing factors') == actual.metadata.get('smoothing factors')

# test files for AVIRIS-C toRGB test
test_toRGB_AVC_imageFilename = 'f080702t01p00r08rdn_c_sc01_ort_img_123_456.hdr'
test_toRGB_AVC_rgbFilename = 'f080702t01p00r08rdn_c_sc01_ort_img_123_456_rgb.hdr'
test_toRGB_AVC_testFilename = 'f080702t01p00r08rdn_c_sc01_ort_img_rgb_test.hdr'
test_toRGB_AVC_testImage = 'f080702t01p00r08rdn_c_sc01_ort_img_rgb_test.img'

# tear down AVIRIS-C toRGB test by deleting temporary files
def _test_toRGB_AVC_teardown():
    try:
        os.remove(test_toRGB_AVC_testFilename)
        os.remove(test_toRGB_AVC_testImage)
    except OSError:
        pass

# verify that the RGB converter selects the correct AVIRIS-C bands and updates the metadata
@with_setup(None, _test_toRGB_AVC_teardown)
def test_toRGB_AVC():
    mineral.MineralClassification.toRGB(test_toRGB_AVC_imageFilename, test_toRGB_AVC_testFilename)
    expected = spectral.open_image(test_toRGB_AVC_rgbFilename)
    actual = spectral.open_image(test_toRGB_AVC_testFilename)
    assert numpy.array_equal(expected.asarray(), actual.asarray())
    assert expected.metadata.get('wavelength') == actual.metadata.get('wavelength')
    assert expected.metadata.get('correction factors') == actual.metadata.get('correction factors')
    assert expected.metadata.get('fwhm') == actual.metadata.get('fwhm')
    assert expected.metadata.get('bbl') == actual.metadata.get('bbl')
    assert expected.metadata.get('smoothing factors') == actual.metadata.get('smoothing factors')
