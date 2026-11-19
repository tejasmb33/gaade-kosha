"""Approved-cloud sync planning uses isolated synthetic SQLite data; no remote writes."""
import pytest
from backend.app import create_app,Proverb,APPROVED,dump
from scripts.sync_approved_cloud import plan_sync

def test_sync_preserves_hosted_review_timestamps_and_detects_missing(tmp_path):
    app=create_app(tmp_path,'synthetic-token')
    with app.state.Session.begin() as session:
        row=Proverb(id='existing',proverb_kn='ಕೃತಕ ಪರೀಕ್ಷೆ',literal_meaning='Synthetic literal',contextual_meaning='Synthetic context',verification_status=APPROVED,reviewed_at='hosted-review-time')
        session.add(row);session.flush();record=dump(row)
    record['reviewed_at']='local-review-time'
    missing={**record,'id':'new','proverb_kn':'ಕೃತಕ ಹೊಸ ಪರೀಕ್ಷೆ'}
    with app.state.Session.begin() as session:
        remote,new,unchanged,conflicts=plan_sync(session,[record,missing])
        assert len(remote)==1 and new==[missing] and unchanged==['existing'] and not conflicts
        assert session.get(Proverb,'existing').reviewed_at=='hosted-review-time'

def test_sync_does_not_overwrite_changed_or_pending_hosted_records(tmp_path):
    app=create_app(tmp_path,'synthetic-token')
    with app.state.Session.begin() as session:
        row=Proverb(id='existing',proverb_kn='ಕೃತಕ ಪರೀಕ್ಷೆ',literal_meaning='Synthetic literal',contextual_meaning='Hosted synthetic edit',verification_status='PENDING_VERIFICATION')
        session.add(row);session.flush();record=dump(row)
    record.update(verification_status=APPROVED,contextual_meaning='Local synthetic meaning')
    with app.state.Session.begin() as session:
        _,new,unchanged,conflicts=plan_sync(session,[record])
        assert not new and not unchanged
        assert set(conflicts[0]['fields'])=={'contextual_meaning','verification_status'}
        assert session.get(Proverb,'existing').contextual_meaning=='Hosted synthetic edit'
        with pytest.raises(ValueError):plan_sync(session,[{**record,'verification_status':'PENDING_VERIFICATION'}])
