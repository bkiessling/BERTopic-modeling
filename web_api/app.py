"""Local, single-process API. Model jobs run outside the request/event loop."""
from __future__ import annotations
import io
import json
import logging
import os
from pathlib import Path
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache
from threading import RLock
import time
import tomllib
import zipfile
from typing import Annotated

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import pandas as pd
import plotly.express as px

from modules.upload.delimiter_utils import detect_delimiter
from modules.preprocessing.text_selection import build_text_df
from modules.preprocessing.text_cleaner import clean_text_column, filter_text_column
from modules.modeling.configuration import MODEL_OPTIONS, TrainingConfig, get_default_params
from modules.modeling.encoders import build_encoder
from modules.modeling.train_model import train_bertopic_model
from modules.ui.analysis_state import AnalysisState
from modules.analysis.topic_table import build_topic_table, compute_topic_stats
from modules.analysis.document_table import build_document_table
from modules.analysis.export import build_result_archive
from modules.analysis.topic_naming import NAMING_MODELS, DEFAULT_NAMING_MODEL, name_topics, topic_keywords, check_model_access, TopicNamingError
from modules.viz.topic_similarity import plot_topic_similarity
from modules.viz.bar_chart import _plot_barcharts
from modules.viz.projection import project_documents

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title='Themenstudio', version='1.0.0')
workers = ThreadPoolExecutor(max_workers=1, thread_name_prefix='bertopic')
log = logging.getLogger(__name__)


def records(frame):
    return json.loads(frame.to_json(orient='records', force_ascii=False, date_format='iso'))


def key_binding():
    for path in (ROOT/'.streamlit/secrets.toml', Path.home()/'.streamlit/secrets.toml'):
        if not path.is_file():
            continue
        try:
            with path.open('rb') as source:
                values = tomllib.load(source)
        except (OSError, tomllib.TOMLDecodeError):
            raise HTTPException(400, 'Streamlit-Secrets konnten nicht gelesen werden. TOML-Syntax prüfen.') from None
        for name in ('BERTOPIC_OPENAI_API_KEY', 'OPENAI_API_KEY'):
            if str(values.get(name, '')).strip():
                return str(values[name]).strip(), f'Streamlit-Secrets · {name}'
    for name in ('BERTOPIC_OPENAI_API_KEY', 'OPENAI_API_KEY'):
        if os.environ.get(name, '').strip():
            return os.environ[name].strip(), f'Umgebungsvariable · {name}'
    return '', ''


@dataclass
class Workspace:
    raw: pd.DataFrame | None = None
    file_name: str = ''
    cleaned: pd.DataFrame | None = None
    text_columns: list = field(default_factory=list)
    preprocessing: dict = field(default_factory=dict)
    cleaning_stats: dict = field(default_factory=dict)
    analysis: AnalysisState | None = None
    coordinates: object = None
    tsne_coordinates: object = None
    job: dict = field(default_factory=lambda: {'status':'idle', 'progress':0, 'message':'', 'error':'', 'warning':'', 'kind':''})
    touched: float = field(default_factory=time.time)
    lock: RLock = field(default_factory=RLock)


spaces: dict[str, Workspace] = {}
spaces_lock = RLock()


def workspace(token):
    with spaces_lock:
        state = spaces.get(token or '')
        if state is None:
            raise HTTPException(404, 'Arbeitsbereich nicht mehr verfügbar. Bitte einen neuen Arbeitsbereich starten.')
        state.touched = time.time()
        return state


def idle(state):
    if state.job['status'] in ('queued', 'running'):
        raise HTTPException(409, 'Bitte den laufenden Vorgang abwarten.')


def analysis_required(state):
    if state.analysis is None:
        raise HTTPException(409, 'Bitte zuerst ein Modell trainieren.')
    return state.analysis


def run_job(state, kind, task):
    with state.lock:
        idle(state)
        state.job = {'status':'queued', 'progress':0, 'message':'Wird vorbereitet …', 'error':'', 'warning':'', 'kind':kind}
    def report(percent, message):
        with state.lock:
            state.job.update(progress=percent, message=message)
    def execute():
        with state.lock:
            state.job['status'] = 'running'
        try:
            warning = task(report)
        except (ValueError, TopicNamingError) as exc:
            with state.lock:
                state.job.update(status='failed', error=str(exc), message='Vorgang nicht abgeschlossen')
        except Exception:
            log.exception('Local workbench job failed')
            with state.lock:
                state.job.update(status='failed', error='Der Vorgang ist fehlgeschlagen. Serverprotokoll und Modellzugriff prüfen.', message='Vorgang nicht abgeschlossen')
        else:
            with state.lock:
                state.job.update(status='completed', progress=100, message='Abgeschlossen', warning=warning or '')
    initial = {'status':'queued', 'progress':0, 'message':'Wird vorbereitet …', 'error':'', 'warning':'', 'kind':kind}
    workers.submit(execute)
    return initial


@lru_cache(maxsize=2)
def encoder(name):
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
    return build_encoder(name, device)


@app.get('/api/health')
def health():
    return {'status':'ok'}


@app.get('/api/capabilities')
def capabilities():
    key, source = key_binding()
    return {'models':[{'id':name,'label':option.label,'languages':option.languages,'description':option.description}
                      for name,option in MODEL_OPTIONS.items()], 'naming_models':NAMING_MODELS,
            'key_present':bool(key),'key_source':source,'default_naming_model':DEFAULT_NAMING_MODEL}


@app.post('/api/workspaces')
def create_workspace():
    with spaces_lock:
        expired = [token for token, state in spaces.items() if time.time()-state.touched > 7200 and state.job['status'] not in ('queued','running')]
        for token in expired:
            del spaces[token]
        if len(spaces) >= 20:
            raise HTTPException(429, 'Zu viele lokale Arbeitsbereiche geöffnet. Server neu starten oder alte Sitzungen auslaufen lassen.')
        token = secrets.token_urlsafe(32)
        spaces[token] = Workspace()
    return {'id':token}


@app.get('/api/workspace')
def get_workspace(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    imported = None if state.raw is None else {
        'file_name':state.file_name,'rows':len(state.raw),'columns':state.raw.columns.tolist(),
        'text_columns':state.raw.select_dtypes(include=['object','string']).columns.tolist(),
        'delimiter':None,'preview':records(state.raw.head(8)),
    }
    cleaned = None if state.cleaned is None else {
        'rows':len(state.cleaned),'rows_before':state.cleaning_stats.get('rows_before',len(state.cleaned)),
        'average_length':round(float(state.cleaned.text.str.len().mean()),1),
        'preview':records(state.cleaned.head(8)),
        'defaults':get_default_params(len(state.cleaned),float(state.cleaned.text.str.len().mean())),
    }
    return {'file_name':state.file_name,'imported':state.raw is not None,'cleaned':state.cleaned is not None,
            'has_results':state.analysis is not None,'job':dict(state.job),'import_result':imported,'clean_result':cleaned,
            'text_columns':state.text_columns,'id_column':state.preprocessing.get('id_column','ID generieren'),
            'preprocessing':state.preprocessing}



@app.post('/api/import')
def import_file(x_workspace_id: Annotated[str, Header()], file: UploadFile = File(...), delimiter: str | None = Form(None)):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        content = file.file.read(25*1024*1024+1)
        if len(content) > 25*1024*1024:
            raise HTTPException(413, 'Datei ist größer als 25 MB.')
        try:
            if (file.filename or '').lower().endswith('.csv'):
                text = content.decode('utf-8-sig')
                sep = delimiter or detect_delimiter(text)
                if sep not in (',',';','\t'):
                    sep = ','
                frame = pd.read_csv(io.StringIO(text), sep=sep)
            elif (file.filename or '').lower().endswith('.xlsx'):
                frame = pd.read_excel(io.BytesIO(content))
                sep = None
            else:
                raise HTTPException(400, 'Bitte eine CSV- oder XLSX-Datei auswählen.')
        except (ValueError, UnicodeError, OSError, zipfile.BadZipFile):
            raise HTTPException(400, 'Datei konnte nicht gelesen werden. UTF-8, Dateiformat und Trennzeichen prüfen.') from None
        if frame.empty:
            raise HTTPException(400, 'Die Datei enthält keine Datenzeilen.')
        frame.columns = frame.columns.map(str)
        if not frame.columns.is_unique:
            raise HTTPException(400, 'Spaltennamen müssen eindeutig sein.')
        state.raw, state.file_name = frame, file.filename or 'Upload'
        state.cleaned, state.analysis, state.coordinates, state.tsne_coordinates = None, None, None, None
    return {'file_name':state.file_name,'rows':len(frame),'columns':frame.columns.tolist(),
            'text_columns':frame.select_dtypes(include=['object','string']).columns.tolist(),
            'delimiter':sep,'preview':records(frame.head(8))}


class CleanRequest(BaseModel):
    text_columns: list[str]
    id_column: str = 'ID generieren'
    sample_percentage: int = Field(100, ge=1, le=100)
    custom_stopwords: str = Field('', max_length=10000)


@app.post('/api/clean')
def clean(body: CleanRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        if state.raw is None:
            raise HTTPException(409, 'Bitte zuerst eine Datei importieren.')
        if not body.text_columns or len(set(body.text_columns)) != len(body.text_columns) or any(col not in state.raw.columns for col in body.text_columns):
            raise HTTPException(400, 'Mindestens eine gültige Textspalte auswählen.')
        if body.id_column != 'ID generieren' and (body.id_column not in state.raw.columns or body.id_column in body.text_columns):
            raise HTTPException(400, 'ID-Spalte muss vorhanden und von den Textspalten verschieden sein.')
        selected = build_text_df(state.raw, body.text_columns, body.id_column)
        if body.sample_percentage < 100:
            selected = selected.sample(frac=body.sample_percentage/100, random_state=42).reset_index(drop=True)
        frame = filter_text_column(clean_text_column(selected, 'text'), 'text')
        words = {word.strip().lower() for word in body.custom_stopwords.split(',') if word.strip()}
        if words:
            # Exact token/phrase matching, including start/end of text.
            for word in words:
                import re
                frame['text'] = frame.text.str.replace(r'(?<!\w)'+re.escape(word)+r'(?!\w)', ' ', regex=True)
            frame['text'] = frame.text.str.replace(r'\s+', ' ', regex=True).str.strip()
            frame = filter_text_column(frame, 'text')
        if frame.empty:
            raise HTTPException(400, 'Nach der Bereinigung sind keine Texte übrig.')
        if frame.id.isna().any():
            raise HTTPException(400, 'Die ID-Spalte enthält fehlende Werte. IDs generieren oder eine vollständige Spalte wählen.')
        state.cleaned, state.analysis, state.coordinates, state.tsne_coordinates = frame.reset_index(drop=True), None, None, None
        state.text_columns, state.preprocessing = body.text_columns, body.model_dump()
        state.cleaning_stats = {'rows_before':len(selected)}
    return {'rows_before':len(selected),'rows':len(frame),'average_length':round(float(frame.text.str.len().mean()),1),
            'preview':records(frame.head(8)),'defaults':get_default_params(len(frame), float(frame.text.str.len().mean()))}


class TrainRequest(BaseModel):
    params: dict


@app.post('/api/train')
def train(body: TrainRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        idle(state)
        if state.cleaned is None:
            raise HTTPException(409, 'Bitte zuerst Texte bereinigen.')
        try:
            config = TrainingConfig.from_dict(body.params)
            errors = config.validate(state.cleaned.text.tolist())
        except (TypeError, KeyError, AttributeError):
            raise HTTPException(400, 'Unvollständige Modellparameter.') from None
        if config.embedding_model not in MODEL_OPTIONS:
            errors.append('Ein Modell aus der Auswahlliste verwenden.')
        if config.name_topics and not key_binding()[0]:
            errors.append('Für die KI-Benennung fehlt ein OpenAI-API-Key.')
        if errors:
            raise HTTPException(400, '\n'.join(errors))
        data = state.cleaned.copy()
    def task(report):
        report(1, 'Lade Embedding-Modell …')
        result = train_bertopic_model(data.text.tolist(), config, encoder(config.embedding_model), on_progress=lambda p,m:report(min(p,90),m))
        analysis = AnalysisState(result, data.id.tolist(), state.text_columns, state.preprocessing)
        warning = ''
        if config.name_topics:
            report(92, 'Benenne Themen anhand der Keywords …')
            try:
                labels = name_topics(topic_keywords(result.model), config.language, key_binding()[0], config.naming_model)
                analysis.set_topic_names(labels, config.naming_model)
            except TopicNamingError as exc:
                warning = str(exc)
        report(95, 'Bereite Dokumentenkarte vor …')
        coordinates = project_documents(result.embeddings)
        with state.lock:
            state.analysis, state.coordinates, state.tsne_coordinates = analysis, coordinates, None
        return warning
    return run_job(state, 'training', task)


@app.get('/api/job')
def get_job(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    with state.lock:
        return dict(state.job)


@app.get('/api/results')
def results(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    info, docs = analysis.named_topic_info(), analysis.result.documents
    n_topics, outliers, average = compute_topic_stats(info, docs)
    return {'topics':records(build_topic_table(info,docs,analysis.result.config.top_n_words)),
            'stats':{'topics':n_topics,'documents':len(docs),'unique_ids':len(set(analysis.ids)), 'outliers':float(outliers),'average':average},
            'parameters':analysis.result.config.to_dict(),'keywords':[{'id':topic,'keywords':words} for topic,words in topic_keywords(analysis.result.model).items()],
            'naming':analysis.naming_metadata,'can_restore':analysis.original_topics is not None}


@app.get('/api/documents')
def documents(x_workspace_id: Annotated[str, Header()], page: int = 0, search: str = '', grouped: bool = False):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    frame = build_document_table(analysis.ids, analysis.result.documents, analysis.result.model.topics_,
                                 analysis.named_topic_info(),'Textbeitrag','ID' if grouped else 'Textbeitrag')
    if search:
        mask = frame.astype(str).apply(lambda column: column.str.contains(search,case=False,regex=False)).any(axis=1)
        frame = frame[mask]
    page = max(0, page)
    return {'rows':records(frame.iloc[page*50:(page+1)*50]),'total':len(frame),'page':page,'page_size':50}


@app.get('/api/charts/{kind}')
def chart(kind: str, x_workspace_id: Annotated[str, Header()], topics: str = '', top_words: int = 5, method: str = 'umap'):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    model = analysis.result.model
    info = analysis.named_topic_info()
    names = analysis.topic_names
    if kind == 'similarity':
        figure = plot_topic_similarity(model, topic_names=names)
    elif kind == 'bars':
        try:
            selected = [int(topic) for topic in topics.split(',') if topic] if topics else info[info.Topic != -1].nlargest(4,'Count').Topic.tolist()
        except ValueError:
            raise HTTPException(400, 'Ungültige Themenauswahl.') from None
        if not 1 <= len(selected) <= 4 or any(topic not in info.Topic.tolist() or topic == -1 for topic in selected):
            raise HTTPException(400, 'Ein bis vier vorhandene Themen auswählen.')
        labels = [f'{topic} · {names.get(topic, model.get_topic_info().set_index("Topic").loc[topic,"Name"])}' for topic in selected]
        figure = _plot_barcharts(model, selected, labels, min(30,max(1,top_words)), 1000, 280*len(selected))
    elif kind == 'network':
        coords = state.coordinates
        if method == 'tsne':
            with state.lock:
                if state.tsne_coordinates is None:
                    state.tsne_coordinates = project_documents(analysis.result.embeddings, 'tsne')
                coords = state.tsne_coordinates
        elif method != 'umap':
            raise HTTPException(400, 'Unbekannte Projektion.')
        labels = {int(row.Topic):f'{int(row.Topic)} · {names.get(int(row.Topic), row.Name)}' for row in info.itertuples()}
        points = pd.DataFrame({'x':coords[:,0],'y':coords[:,1], 'Thema':[labels[topic] for topic in model.topics_]})
        figure = px.scatter(points,x='x',y='y',color='Thema',opacity=.7,
                            color_discrete_sequence=['#7560dd','#56a998','#dbab67','#e48599','#6d99cd','#a68ac8'])
        figure.update_traces(marker={'size':7}, hovertemplate='%{fullData.name}<extra></extra>')
        figure.update_layout(xaxis_visible=False,yaxis_visible=False,height=540,legend={'orientation':'h'})
    else:
        raise HTTPException(404, 'Diagramm nicht gefunden.')
    figure.update_layout(font={'family':'Inter, ui-sans-serif, system-ui','color':'#424650'}, paper_bgcolor='rgba(0,0,0,0)',
                         plot_bgcolor='rgba(0,0,0,0)', margin={'l':40,'r':20,'t':45,'b':60})
    return json.loads(figure.to_json())


class NamingRequest(BaseModel):
    model: str = DEFAULT_NAMING_MODEL


@app.post('/api/openai/check')
def check_openai(body: NamingRequest, x_workspace_id: Annotated[str, Header()]):
    workspace(x_workspace_id)
    try:
        check_model_access(key_binding()[0], body.model)
    except TopicNamingError as exc:
        raise HTTPException(400, str(exc)) from None
    return {'message':'Key akzeptiert; Modell sichtbar. Responses-Berechtigung und Guthaben werden beim Benennen geprüft.'}


@app.post('/api/name')
def name(body: NamingRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    if not key_binding()[0]:
        raise HTTPException(400, 'Kein OpenAI-API-Key vorhanden.')
    def task(report):
        report(20, 'Benenne Themen anhand der Keywords …')
        labels = name_topics(topic_keywords(analysis.result.model),analysis.result.config.language,key_binding()[0],body.model)
        analysis.set_topic_names(labels,body.model)
    return run_job(state,'naming',task)


class OutlierRequest(BaseModel):
    threshold: float = Field(.05, ge=0, le=.5)


@app.post('/api/outliers')
def outliers(body: OutlierRequest, x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    def task(report):
        report(20, 'Ordne Ausreißer neu zu …')
        if not analysis.reduce_outliers(body.threshold):
            return 'Keine Ausreißer vorhanden.'
    return run_job(state,'outliers',task)


@app.post('/api/outliers/restore')
def restore(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    def task(report):
        report(20, 'Stelle ursprüngliche Zuordnungen wieder her …')
        if not analysis.restore_outliers():
            return 'Keine ursprünglichen Zuordnungen gespeichert.'
    return run_job(state,'restore',task)


@app.get('/api/export')
def export(x_workspace_id: Annotated[str, Header()]):
    state = workspace(x_workspace_id)
    analysis = analysis_required(state)
    content = build_result_archive(analysis.result.documents,analysis.ids,analysis.result.model.topics_,analysis.named_topic_info(),
                                   analysis.result.config.to_dict(),{'trained_at':analysis.trained_at,'text_columns':analysis.text_columns,
                                   'preprocessing':analysis.preprocessing,'outlier_thresholds':analysis.outlier_thresholds,'topic_naming':analysis.naming_metadata})
    return Response(content,media_type='application/zip',headers={'Content-Disposition':'attachment; filename="bertopic-results.zip"'})


if (ROOT/'frontend/dist').is_dir():
    app.mount('/', StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
