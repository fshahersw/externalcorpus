"""Install two independently reviewed follow-up portraits; preserve existing identities and rollback."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'sources/judge_portrait_followup_20260919'
TARGET=ROOT/'sources/judge_presentation_20260918'
OUT=Path(__file__).resolve().parent/'portrait_followup_integration'
sys.path.insert(0,str(ROOT/'delivery/archive-directory'))
import judges
from pending_titles import writer_lock


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def main():
    assert not (OUT/'receipt.json').exists(), 'Preserve prior follow-up integration receipt'
    gate=read(SOURCE/'validation.json');assert gate['status']=='passed'
    for name,expected in gate['files'].items():
        path=SOURCE/name;assert path.parent==SOURCE and sha(path)==expected['sha256'] and path.stat().st_size==expected['bytes']
    accepted={row['entity_id']:row for row in rows(SOURCE/'accepted_links.jsonl')}
    proposed=rows(SOURCE/'portraits.append.jsonl');assert len(proposed)==len(accepted)==2
    with writer_lock(judges.DB):
        manifest=TARGET/'portraits.jsonl';before=manifest.read_bytes();prior=rows(manifest)
        existing={row['entity_id']:row for row in prior};staged=[]
        for row in proposed:
            match=accepted[row['entity_id']]
            image=(ROOT/match['path']).resolve();destination=(ROOT/row['path']).resolve()
            assert image.is_relative_to((SOURCE/'images').resolve()) and destination.is_relative_to((TARGET/'images').resolve())
            assert sha(image)==match['sha256']==row['sha256'] and row['path']==match['proposed_presentation_path']
            evidence=(ROOT/match['identity_evidence_path']).resolve()
            assert evidence.is_relative_to((SOURCE/'evidence').resolve()) and sha(evidence)==match['identity_evidence_sha256']==row['provenance']['identity_evidence_sha256']
            judges.validated_image(match,SOURCE/'images')
            profile=judges.profile(row['entity_id']);assert profile and profile['entity_id']==row['entity_id']
            if row['entity_id'] in existing:
                assert existing[row['entity_id']]==row
                continue
            assert not profile['photo_url'], 'Do not replace an installed portrait'
            staged.append((image,destination,row))
        OUT.mkdir(parents=True,exist_ok=True)
        backup=OUT/'prior_portraits.jsonl'
        if not backup.exists():backup.write_bytes(before)
        database_backup=OUT/'prior_profiles.sqlite3'
        if not database_backup.exists():shutil.copyfile(judges.DB,database_backup)
        for image,destination,row in staged:
            if destination.exists():assert sha(destination)==row['sha256']
            else:shutil.copyfile(image,destination)
            judges.validated_image(row,TARGET/'images');existing[row['entity_id']]=row
        try:
            tmp=TARGET/'portraits.building.jsonl'
            tmp.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in existing.values()),encoding='utf8')
            tmp.replace(manifest)
            summary=judges.build()
            assert summary['profiles']==10698 and summary['profiles_with_photos']==51 and summary['analysis_records']==708
            assert judges.listing({'has':'photo'})['total']==51
            for row in proposed:
                assert judges.profile(row['entity_id'])['photo_url']=='/judge-images/'+row['id']
                assert judges.image_file(row['id'])
        except Exception:
            manifest.write_bytes(before)
            shutil.copyfile(database_backup,judges.DB)
            raise
    receipt={'status':'passed','integrated_at':datetime.now(timezone.utc).isoformat(),'new_portraits':len(staged),
             'profiles_with_photos':51,'browse_profiles':10698,'identity_merges_added':0,'separate_profiles_added':0,
             'held_unlinked_portraits_from_prior_batch':9,'manifest_sha256':sha(manifest),'database_sha256':sha(judges.DB),
             'source_manifest_sha256':sha(SOURCE/'accepted_links.jsonl'),'main_directory_rebuilt':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt))


if __name__=='__main__':main()
