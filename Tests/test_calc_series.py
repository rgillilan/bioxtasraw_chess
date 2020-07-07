import os
import copy

import pytest

raw_path = os.path.abspath(os.path.join('.', __file__, '..', '..'))
if raw_path not in os.sys.path:
    os.sys.path.append(raw_path)

import bioxtasraw.RAWAPI as raw

@pytest.fixture(scope="package")
def bsa_series():
    series = raw.load_series([os.path.join('.', 'data',
            'BSA_001.hdf5')])[0]
    return series

@pytest.fixture(scope="function")
def clean_bsa_series(bsa_series):
    series = raw.load_series([os.path.join('.', 'data',
            'clean_BSA_001.hdf5')])[0]
    return series

@pytest.fixture(scope="package")
def int_baseline_series():
    series = raw.load_series([os.path.join('.', 'data',
            'short_profile_001.hdf5')])[0]
    return series

@pytest.fixture(scope="function")
def clean_baseline_series(int_baseline_series):
    series = copy.deepcopy(int_baseline_series)
    return series

def test_svd(bsa_series):
    svd_s, svd_U, svd_V = raw.svd(bsa_series)
    assert svd_s[0] == 7474.750264659797

def test_svd_list(bsa_series):
    sasms = bsa_series.subtracted_sasm_list

    svd_s, svd_U, svd_V = raw.svd(sasms)
    assert svd_s[0] == 7474.750264659797

def test_efa(bsa_series):
    efa_profiles, converged, conv_data, rotation_data = raw.efa(bsa_series,
        [[130, 187], [149, 230]], framei=130, framef=230)

    assert converged
    assert conv_data['final_step'] == 9.254595973975021e-13
    assert len(efa_profiles) == 2
    assert efa_profiles[0].getI().sum() == 75885.43573919893

def test_efa_list(bsa_series):
    sasms = bsa_series.subtracted_sasm_list

    efa_profiles, converged, conv_data, rotation_data = raw.efa(sasms,
        [[130, 187], [149, 230]], framei=130, framef=230)

    assert converged
    assert conv_data['final_step'] == 9.254595973975021e-13
    assert len(efa_profiles) == 2
    assert efa_profiles[0].getI().sum() == 75885.43573919893

def test_find_buffer_range(bsa_series):
    success, region_start, region_end = raw.find_buffer_range(bsa_series)

    assert success
    assert region_start == 18
    assert region_end == 53

def test_find_buffer_range_list(bsa_series):
    sasms = bsa_series.getAllSASMs()

    success, region_start, region_end = raw.find_buffer_range(sasms)

    assert success
    assert region_start == 18
    assert region_end == 53

def test_validate_buffer_range_good(bsa_series):
    (valid, similarity_results, svd_results,
        intI_results) = raw.validate_buffer_range(bsa_series, [[18, 53]])

    assert valid
    assert similarity_results['all_similar']
    assert similarity_results['low_q_similar']
    assert similarity_results['high_q_similar']
    assert svd_results['svals'] == 1
    assert intI_results['intI_valid']
    assert intI_results['smoothed_intI_valid']
    assert intI_results['intI_pval'] == 0.33394404805178013
    assert intI_results['smoothed_intI_pval'] == 0.02474248231802627

def test_validate_buffer_region_bad(bsa_series):
    (valid, similarity_results, svd_results,
        intI_results) = raw.validate_buffer_range(bsa_series, [[50, 100]])

    assert not valid
    assert not similarity_results['all_similar']
    assert similarity_results['low_q_similar']
    assert not similarity_results['high_q_similar']
    assert similarity_results['all_outliers'][0] == 34
    assert similarity_results['high_q_outliers'][0] == 46
    assert svd_results['svals'] == 1
    assert not intI_results['intI_valid']
    assert not intI_results['smoothed_intI_valid']
    assert intI_results['intI_pval'] == 0.0007815284021663028
    assert intI_results['smoothed_intI_pval'] == 2.8531443061690295e-19

def test_validate_buffer_range_list(bsa_series):
    sasms = bsa_series.getAllSASMs()

    (valid, similarity_results, svd_results,
        intI_results) = raw.validate_buffer_range(sasms, [[18, 53]])

    assert valid
    assert similarity_results['all_similar']
    assert similarity_results['low_q_similar']
    assert similarity_results['high_q_similar']
    assert svd_results['svals'] == 1
    assert intI_results['intI_valid']
    assert intI_results['smoothed_intI_valid']
    assert intI_results['intI_pval'] == 0.33394404805178013
    assert intI_results['smoothed_intI_pval'] == 0.02474248231802627

def test_set_buffer_range(clean_bsa_series):
    (sub_profiles, rg, rger, i0, i0er, vcmw, vcmwer,
        vpmw) = raw.set_buffer_range(clean_bsa_series, [[18, 53]])

    assert len(sub_profiles) == len(clean_bsa_series.getAllSASMs())
    assert rg[200] == 27.883148917654523
    assert rger[200] == 0.04393097355157037
    assert i0[200] == 138.32018141846123
    assert vcmw[200] == 65.55494106050756
    assert vpmw[200] == 68.91548154696382
    assert all(clean_bsa_series.getRg()[0] == rg)
    assert clean_bsa_series.getIntISub().sum() == 331.3353154360302

def test_series_calc(bsa_series):
    sasms = bsa_series.subtracted_sasm_list

    rg, rger, i0, i0er, vcmw, vcmwer, vpmw = raw.series_calc(sasms)

    assert rg[200] == 27.883148917654523
    assert rger[200] == 0.04393097355157037
    assert i0[200] == 138.32018141846123
    assert vcmw[200] == 65.55494106050756
    assert vpmw[200] == 68.91548154696382

def test_find_sample_range(bsa_series):
    success, region_start, region_end = raw.find_sample_range(bsa_series)

    assert success
    assert region_start == 188
    assert region_end == 206

def test_find_sample_range_list(bsa_series):
    sasms = bsa_series.subtracted_sasm_list
    rg = bsa_series.getRg()[0]
    vcmw = bsa_series.getVcMW()[0]
    vpmw = bsa_series.getVpMW()[0]

    success, region_start, region_end = raw.find_sample_range(sasms, rg=rg,
        vcmw=vcmw, vpmw=vpmw)

    assert success
    assert region_start == 188
    assert region_end == 206

def test_validate_sample_range_good(bsa_series):
    (valid, similarity_results, param_results, svd_results,
        sn_results) = raw.validate_sample_range(bsa_series, [[188, 206]])

    assert valid
    assert similarity_results['all_similar']
    assert similarity_results['low_q_similar']
    assert similarity_results['high_q_similar']
    assert svd_results['svals'] == 1
    assert param_results['param_valid']
    assert param_results['rg_valid']
    assert param_results['vcmw_valid']
    assert param_results['vpmw_valid']
    assert param_results['rg_pval'] == 0.9488461264555137
    assert param_results['vcmw_pval'] == 0.3438801731989136
    assert param_results['vpmw_pval'] == 0.6472068934597522
    assert sn_results['sn_valid']

def test_validate_sample_range_bad(bsa_series):
    (valid, similarity_results, param_results, svd_results,
        sn_results) = raw.validate_sample_range(bsa_series, [[190, 210]])

    assert not valid
    assert similarity_results['all_similar']
    assert similarity_results['low_q_similar']
    assert similarity_results['high_q_similar']
    assert svd_results['svals'] == 1
    assert not param_results['param_valid']
    assert not param_results['rg_valid']
    assert param_results['vcmw_valid']
    assert not param_results['vpmw_valid']
    assert param_results['rg_pval'] == 0.0009457098107349513
    assert param_results['vcmw_pval'] == 0.7625997832797398
    assert param_results['vpmw_pval'] == 0.018076642193560675
    assert sn_results['sn_valid']

def test_validate_sample_range_list(bsa_series):
    sasms = bsa_series.subtracted_sasm_list
    rg = bsa_series.getRg()[0]
    vcmw = bsa_series.getVcMW()[0]
    vpmw = bsa_series.getVpMW()[0]

    (valid, similarity_results, param_results, svd_results,
        sn_results) = raw.validate_sample_range(sasms, [[188, 206]], rg=rg,
        vcmw=vcmw, vpmw=vpmw)

    assert valid
    assert similarity_results['all_similar']
    assert similarity_results['low_q_similar']
    assert similarity_results['high_q_similar']
    assert svd_results['svals'] == 1
    assert param_results['param_valid']
    assert param_results['rg_valid']
    assert param_results['vcmw_valid']
    assert param_results['vpmw_valid']
    assert param_results['rg_pval'] == 0.9488461264555137
    assert param_results['vcmw_pval'] == 0.3438801731989136
    assert param_results['vpmw_pval'] == 0.6472068934597522
    assert sn_results['sn_valid']

def test_set_sampe_range(bsa_series):
    sub_profile = raw.set_sample_range(bsa_series, [[188, 206]])

    assert sub_profile.getI().sum() == 11758.431580249562

def test_find_baseline_range_integral(int_baseline_series):
    (start_found, end_found, start_range,
        end_range) = raw.find_baseline_range(int_baseline_series)

    assert start_found
    assert end_found
    assert start_range[0] == 42
    assert start_range[1] == 71
    assert end_range[0] == 318
    assert end_range[1] == 347

def test_find_baseline_range_integral_list(int_baseline_series):
    sasms = int_baseline_series.subtracted_sasm_list

    (start_found, end_found, start_range,
        end_range) = raw.find_baseline_range(sasms)

    assert start_found
    assert not end_found
    assert start_range[0] == 140
    assert start_range[1] == 169

def test_validate_baseline_range_integral_good(int_baseline_series):
    (valid, valid_results, similarity_results, svd_results, intI_results,
        other_results) = raw.validate_baseline_range(int_baseline_series,
        [42, 71], [318, 347])

    assert valid
    assert similarity_results[0]['all_similar']
    assert similarity_results[0]['low_q_similar']
    assert similarity_results[0]['high_q_similar']
    assert svd_results[0]['svals'] == 1
    assert intI_results[0]['intI_valid']
    assert intI_results[0]['smoothed_intI_valid']
    assert intI_results[0]['intI_pval'] == 0.2388039563971044
    assert intI_results[0]['smoothed_intI_pval'] == 0.10656462177179266
    assert similarity_results[1]['all_similar']
    assert similarity_results[1]['low_q_similar']
    assert similarity_results[1]['high_q_similar']
    assert svd_results[1]['svals'] == 1
    assert intI_results[1]['intI_valid']
    assert intI_results[1]['smoothed_intI_valid']
    assert intI_results[1]['intI_pval'] == 0.3572478396366079
    assert intI_results[1]['smoothed_intI_pval'] == 0.06588236359826605

def test_validate_baseline_range_integral_bad(int_baseline_series):
    (valid, valid_results, similarity_results, svd_results, intI_results,
        other_results) = raw.validate_baseline_range(int_baseline_series,
        [50, 80], [320, 350])

    assert not valid
    assert similarity_results[0]['all_similar']
    assert similarity_results[0]['low_q_similar']
    assert similarity_results[0]['high_q_similar']
    assert svd_results[0]['svals'] == 1
    assert intI_results[0]['intI_valid']
    assert intI_results[0]['smoothed_intI_valid']
    assert intI_results[0]['intI_pval'] == 0.07367410936498585
    assert intI_results[0]['smoothed_intI_pval'] == 0.017991315636281355
    assert similarity_results[1]['all_similar']
    assert similarity_results[1]['low_q_similar']
    assert similarity_results[1]['high_q_similar']
    assert svd_results[1]['svals'] == 1
    assert intI_results[1]['intI_valid']
    assert not intI_results[1]['smoothed_intI_valid']
    assert intI_results[1]['intI_pval'] == 0.26995117121922096
    assert intI_results[1]['smoothed_intI_pval'] == 0.006453749007721673

def test_validate_baseline_range_list(int_baseline_series):
    sasms = int_baseline_series.subtracted_sasm_list
    (valid, valid_results, similarity_results, svd_results, intI_results,
        other_results) = raw.validate_baseline_range(sasms, [42, 71],
        [318, 347])

    assert valid
    assert similarity_results[0]['all_similar']
    assert similarity_results[0]['low_q_similar']
    assert similarity_results[0]['high_q_similar']
    assert svd_results[0]['svals'] == 1
    assert intI_results[0]['intI_valid']
    assert intI_results[0]['smoothed_intI_valid']
    assert intI_results[0]['intI_pval'] == 0.2388039563971044
    assert intI_results[0]['smoothed_intI_pval'] == 0.10656462177179266
    assert similarity_results[1]['all_similar']
    assert similarity_results[1]['low_q_similar']
    assert similarity_results[1]['high_q_similar']
    assert svd_results[1]['svals'] == 1
    assert intI_results[1]['intI_valid']
    assert intI_results[1]['smoothed_intI_valid']
    assert intI_results[1]['intI_pval'] == 0.3572478396366079
    assert intI_results[1]['smoothed_intI_pval'] == 0.06588236359826605

# def test_validate_baseline_range_linear_good(int_baseline_series):
#     (valid, valid_results, similarity_results, svd_results, intI_results,
#         other_results) = raw.validate_baseline_range(int_baseline_series,
#         [42, 71], [318, 347], 'Linear')

#     assert valid
#     assert similarity_results[0]['all_similar']
#     assert similarity_results[0]['low_q_similar']
#     assert similarity_results[0]['high_q_similar']
#     assert svd_results[0]['svals'] == 1
#     assert intI_results[0]['intI_valid']
#     assert intI_results[0]['smoothed_intI_valid']
#     assert intI_results[0]['intI_pval'] == 0.2388039563971044
#     assert intI_results[0]['smoothed_intI_pval'] == 0.10656462177179266
#     assert similarity_results[1]['all_similar']
#     assert similarity_results[1]['low_q_similar']
#     assert similarity_results[1]['high_q_similar']
#     assert svd_results[1]['svals'] == 1
#     assert intI_results[1]['intI_valid']
#     assert intI_results[1]['smoothed_intI_valid']
#     assert intI_results[1]['intI_pval'] == 0.3572478396366079
#     assert intI_results[1]['smoothed_intI_pval'] == 0.06588236359826605

def test_validate_baseline_range_linear_bad(int_baseline_series):
    (valid, valid_results, similarity_results, svd_results, intI_results,
        other_results) = raw.validate_baseline_range(int_baseline_series,
        [0, 10], [390, 400], 'Linear')

    assert not valid
    assert not other_results[1]['fit_valid']

def test_set_baseline_correction_integral(clean_baseline_series):
    (bl_cor_profiles, rg, rger, i0, i0er, vcmw, vcmwer, vpmw, bl_corr,
        fit_results) = raw.set_baseline_correction(clean_baseline_series,
        [42, 71], [318, 347], 'Integral')

    assert rg[200] == 27.72702098139628
    assert rger[200] == 0.05435118847512014
    assert all(rg == clean_baseline_series.getRg()[0])
    assert clean_baseline_series.getIntIBCSub().sum() == 0.1031091826570453

def test_set_baseline_correction_linear(clean_baseline_series):
    (bl_cor_profiles, rg, rger, i0, i0er, vcmw, vcmwer, vpmw, bl_corr,
        fit_results) = raw.set_baseline_correction(clean_baseline_series,
        [0, 10], [390, 400], 'Linear')

    assert rg[200] == 27.671983516407735
    assert rger[200] == 0.054747246997416635
    assert all(rg == clean_baseline_series.getRg()[0])
    assert clean_baseline_series.getIntIBCSub().sum() == 0.10684702672323632
