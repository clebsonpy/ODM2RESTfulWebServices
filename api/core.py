# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.core.management import settings

from odm2api.ODMconnection import dbconnection
from odm2api.ODM2.services.readService import ReadODM2
import odm2api.ODM2.models as odm2_models

from utils import get_vals

from models import (
    Affiliation,
    Organization,
    People,
    Result,
    Variable,
    Unit,
    FeatureAction,
    ProcessingLevel,
    TaxonomicClassifier,
    SamplingFeatures,
    DataSets
)

SESSION_FACTORY = dbconnection.createConnection(**settings.ODM2DATABASE)
READ = ReadODM2(SESSION_FACTORY)


def db_check():
    db_session = SESSION_FACTORY.getSession()
    try:
        db_session.query(odm2_models.SamplingFeatures).first()
    except:
        print('Rolling Back...')
        db_session.rollback()
    finally:
        pass


def get_affiliations(**kwargs):
    db_check()
    ids = None
    if kwargs.get('affiliationID'):
        ids = [int(i) for i in kwargs.get('affiliationID').split(',')]
    person_first = kwargs.get('firstName')
    person_last = kwargs.get('lastName')
    org_code = kwargs.get('organizationCode')

    Affs = READ.getAffiliations(ids=ids,
                         personfirst=person_first,
                         personlast=person_last,
                         orgcode=org_code)

    Aff_list = []

    for aff in Affs:
        aff_dct = get_vals(aff)
        aff_dct.update({
            'Person':get_vals(aff.PersonObj),
            'Organization': None
        })
        if aff.OrganizationObj:
            aff_dct.update({
                'Organization': get_vals(aff.OrganizationObj)
            })

        Aff_list.append(
            Affiliation(aff_dct)
        )

    return Aff_list


def get_people(**kwargs):
    db_check()
    ids = None
    if kwargs.get('peopleID'):
        ids = [int(i) for i in kwargs.get('peopleID').split(',')]
    person_first = kwargs.get('firstName')
    person_last = kwargs.get('lastName')

    Ppl = READ.getPeople(ids=ids,
                         firstname=person_first,
                         lastname=person_last)

    Ppl_list = []
    for person in Ppl:
        ppl_dct = get_vals(person)
        Ppl_list.append(
            People(ppl_dct)
        )

    return Ppl_list


def get_results(**kwargs):
    db_check()
    ids = None
    uuids = None
    if kwargs.get('resultID'):
        ids = [int(i) for i in kwargs.get('resultID').split(',')]
    if kwargs.get('resultUUID'):
        uuids = kwargs.get('resultUUID').split(',')
    result_type = kwargs.get('resultType')
    act_id = kwargs.get('actionID')
    sf_id = kwargs.get('samplingFeatureID')
    var_id = kwargs.get('variableID')
    sim_id = kwargs.get('simulationID')

    Results = READ.getResults(ids=ids,
                              type=result_type,
                              uuids=uuids,
                              actionid=act_id,
                              simulationid=sim_id,
                              sfid=sf_id,
                              variableid=var_id,
                              siteid=None)

    Results_list = []
    for res in Results:
        res_dct = get_vals(res)

        # Get Feature Action ----
        feat_act_dct = get_vals(res.FeatureActionObj)
        feat_act_dct.update({
            'SamplingFeature': get_vals(res.FeatureActionObj.SamplingFeatureObj),
            'Action': get_vals(res.FeatureActionObj.ActionObj)
        })
        feat_act = FeatureAction(feat_act_dct)
        # ------------------------

        res_dct.update({
            'FeatureAction': feat_act,
            'ProcessingLevel': get_vals(res.ProcessingLevelObj),
            'TaxonomicClassifier': None,
            'Unit': get_vals(res.UnitsObj),
            'Variable': get_vals(res.VariableObj)
        })

        if res.TaxonomicClassifierObj:
            res_dct.update({
                'TaxonomicClassifier': get_vals(res.TaxonomicClassifierObj)
            })

        Results_list.append(
            Result(res_dct)
        )

    return Results_list


def get_samplingfeatures(**kwargs):
    db_check()
    ids = None
    codes = None
    uuids = None
    if kwargs.get('samplingFeatureID'):
        ids = [int(i) for i in kwargs.get('samplingFeatureID').split(',')]
    if kwargs.get('samplingFeatureUUID'):
        uuids = kwargs.get('samplingFeatureUUID').split(',')
    if kwargs.get('samplingFeatureCode'):
        codes = kwargs.get('samplingFeatureCode').split(',')

    sf_type = kwargs.get('samplingFeatureType')
    res = kwargs.get('results')

    if type(res) in [str, unicode]:
        if res.upper() == 'TRUE':
            res = True
        else:
            res = False

    sampling_features = READ.getSamplingFeatures(ids=ids,
                                                 codes=codes,
                                                 uuids=uuids,
                                                 type=sf_type,
                                                 wkt=None,
                                                 results=res)

    sf_list = []
    for sf in sampling_features:
        sf_dct = get_vals(sf)
        sf_list.append(
            SamplingFeatures(sf_dct)
        )

    return sf_list


def get_datasets(**kwargs):
    codes = kwargs.get('datasetCode')
    uuids = kwargs.get('datasetUUID')

    if codes:
        codes = codes.split(',')
    if uuids:
        uuids = uuids.split(',')

    datasets = READ.getDataSets(codes=codes, uuids=uuids)
    ds_list = []
    for ds in datasets:
        ds_dct = get_vals(ds)
        ds_list.append(
            DataSets(ds_dct)
        )

    return ds_list


def get_resultvalues(**kwargs):
    # Result Values doesn't use model,
    # it outputs dataframe,
    # therefore can be serialized directly

    ids = kwargs.get('resultID')
    starttime = kwargs.get('beginDate')
    endtime = kwargs.get('endDate')

    if ids:
        ids = [int(i) for i in ids.split(',')]

    result_values = READ.getResultValues(resultids=ids,
                                         starttime=starttime,
                                         endtime=endtime)
    res = READ.getResults(ids=ids)[0]
    res_type = res.ResultTypeCV.lower()

    return [r.to_dict() for idx, r in result_values.iterrows()], res_type
