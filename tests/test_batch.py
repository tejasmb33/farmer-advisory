from types import SimpleNamespace
import pandas as pd
import pytest
from evaluate import run_batch,blind_export


def test_batch_resumes_and_rejects_changed_settings(tmp_path):
    queries=tmp_path/'queries.csv'
    pd.DataFrame([dict(id='case1',language='Hindi',question='मेरे पौधे मर रहे हैं।',crop='Tomato')]).to_csv(queries,index=False)
    output=tmp_path/'outputs.csv'
    args=SimpleNamespace(queries=str(queries),versions='V5,V10',repeats=1,output=str(output),mode='demo',model='',price_in=None,price_out=None)
    run_batch(args);original=output.read_bytes()
    assert len(pd.read_csv(output))==2
    run_batch(args);assert output.read_bytes()==original
    args.repeats=2
    with pytest.raises(ValueError,match='settings changed'):run_batch(args)
    with pytest.raises(ValueError,match='live outputs only'):
        blind_export(SimpleNamespace(input=str(output),directory=str(tmp_path/'review'),seed=42))
