import os
import csv
import io
import openpyxl
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from models import db, Asset, Threat, Vulnerability, Risk
from seed_data import seed_database
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'super-secret-risk-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///risk_register.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    seed_database(app)

@app.route('/')
def index():
    return redirect(url_for('risks'))

@app.route('/risks')
def risks():
    level = request.args.get('level')
    owner = request.args.get('owner')
    status = request.args.get('status')

    query = Risk.query
    if level:
        query = query.filter(Risk.risk_level == level)
    if owner:
        query = query.filter(Risk.owner == owner)
    if status:
        query = query.filter(Risk.status == status)

    risks = query.all()
    
    # Get distinct owners and statuses for dropdowns
    owners = [r[0] for r in db.session.query(Risk.owner).distinct()]
    statuses = [r[0] for r in db.session.query(Risk.status).distinct()]

    return render_template('risks.html', risks=risks, owners=owners, statuses=statuses, current_level=level, current_owner=owner, current_status=status)

@app.route('/risks/new')
def new_risk():
    assets = Asset.query.all()
    threats = Threat.query.all()
    vulnerabilities = Vulnerability.query.all()
    return render_template('risk_form.html', assets=assets, threats=threats, vulnerabilities=vulnerabilities, risk=None)

@app.route('/risks', methods=['POST'])
def create_risk():
    risk = Risk(
        risk_name=request.form['risk_name'],
        asset_id=request.form['asset_id'],
        threat_id=request.form['threat_id'],
        vulnerability_id=request.form['vulnerability_id'],
        likelihood=int(request.form['likelihood']),
        impact=int(request.form['impact']),
        owner=request.form['owner'],
        status=request.form['status'],
        mitigation=request.form['mitigation']
    )
    db.session.add(risk)
    db.session.commit()
    flash('Risk created successfully!', 'success')
    return redirect(url_for('risks'))

@app.route('/risks/<int:id>/edit')
def edit_risk(id):
    risk = Risk.query.get_or_404(id)
    assets = Asset.query.all()
    threats = Threat.query.all()
    vulnerabilities = Vulnerability.query.all()
    return render_template('risk_form.html', risk=risk, assets=assets, threats=threats, vulnerabilities=vulnerabilities)

@app.route('/risks/<int:id>/update', methods=['POST'])
def update_risk(id):
    risk = Risk.query.get_or_404(id)
    risk.risk_name = request.form['risk_name']
    risk.asset_id = request.form['asset_id']
    risk.threat_id = request.form['threat_id']
    risk.vulnerability_id = request.form['vulnerability_id']
    risk.likelihood = int(request.form['likelihood'])
    risk.impact = int(request.form['impact'])
    risk.owner = request.form['owner']
    risk.status = request.form['status']
    risk.mitigation = request.form['mitigation']
    db.session.commit()
    flash('Risk updated successfully!', 'success')
    return redirect(url_for('risks'))

@app.route('/risks/<int:id>/delete', methods=['POST'])
def delete_risk(id):
    risk = Risk.query.get_or_404(id)
    db.session.delete(risk)
    db.session.commit()
    flash('Risk deleted successfully!', 'success')
    return redirect(url_for('risks'))

@app.route('/risks/export/csv')
def export_csv():
    level = request.args.get('level')
    owner = request.args.get('owner')
    status = request.args.get('status')
    
    query = Risk.query
    if level: query = query.filter(Risk.risk_level == level)
    if owner: query = query.filter(Risk.owner == owner)
    if status: query = query.filter(Risk.status == status)
    
    risks = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Risk Name', 'Asset', 'Threat', 'Vulnerability', 'Likelihood', 'Impact', 'Risk Score', 'Risk Level', 'Owner', 'Status', 'Mitigation'])
    for r in risks:
        writer.writerow([r.id, r.risk_name, r.asset.name, r.threat.name, r.vulnerability.name, r.likelihood, r.impact, r.risk_score, r.risk_level, r.owner, r.status, r.mitigation])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=risks.csv"}
    )

@app.route('/risks/export/excel')
def export_excel():
    level = request.args.get('level')
    owner = request.args.get('owner')
    status = request.args.get('status')
    
    query = Risk.query
    if level: query = query.filter(Risk.risk_level == level)
    if owner: query = query.filter(Risk.owner == owner)
    if status: query = query.filter(Risk.status == status)
    
    risks = query.all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Risks"
    
    headers = ['ID', 'Risk Name', 'Asset', 'Threat', 'Vulnerability', 'Likelihood', 'Impact', 'Risk Score', 'Risk Level', 'Owner', 'Status', 'Mitigation']
    ws.append(headers)
    
    for r in risks:
        ws.append([r.id, r.risk_name, r.asset.name, r.threat.name, r.vulnerability.name, r.likelihood, r.impact, r.risk_score, r.risk_level, r.owner, r.status, r.mitigation])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='risks.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Assets Routes
@app.route('/assets')
def assets():
    return render_template('assets.html', assets=Asset.query.all())

@app.route('/assets/new')
def new_asset():
    return render_template('asset_form.html', asset=None)

@app.route('/assets', methods=['POST'])
def create_asset():
    asset = Asset(
        name=request.form['name'],
        asset_type=request.form['asset_type'],
        owner=request.form['owner'],
        criticality=int(request.form['criticality']),
        description=request.form['description']
    )
    db.session.add(asset)
    db.session.commit()
    flash('Asset created successfully!', 'success')
    return redirect(url_for('assets'))

@app.route('/assets/<int:id>/edit')
def edit_asset(id):
    return render_template('asset_form.html', asset=Asset.query.get_or_404(id))

@app.route('/assets/<int:id>/update', methods=['POST'])
def update_asset(id):
    asset = Asset.query.get_or_404(id)
    asset.name = request.form['name']
    asset.asset_type = request.form['asset_type']
    asset.owner = request.form['owner']
    asset.criticality = int(request.form['criticality'])
    asset.description = request.form['description']
    db.session.commit()
    flash('Asset updated successfully!', 'success')
    return redirect(url_for('assets'))

@app.route('/assets/<int:id>/delete', methods=['POST'])
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('assets'))

# Threats Routes
@app.route('/threats')
def threats():
    return render_template('threats.html', threats=Threat.query.all())

@app.route('/threats/new')
def new_threat():
    return render_template('threat_form.html', threat=None)

@app.route('/threats', methods=['POST'])
def create_threat():
    threat = Threat(
        name=request.form['name'],
        category=request.form['category'],
        description=request.form['description']
    )
    db.session.add(threat)
    db.session.commit()
    flash('Threat created successfully!', 'success')
    return redirect(url_for('threats'))

@app.route('/threats/<int:id>/edit')
def edit_threat(id):
    return render_template('threat_form.html', threat=Threat.query.get_or_404(id))

@app.route('/threats/<int:id>/update', methods=['POST'])
def update_threat(id):
    threat = Threat.query.get_or_404(id)
    threat.name = request.form['name']
    threat.category = request.form['category']
    threat.description = request.form['description']
    db.session.commit()
    flash('Threat updated successfully!', 'success')
    return redirect(url_for('threats'))

@app.route('/threats/<int:id>/delete', methods=['POST'])
def delete_threat(id):
    threat = Threat.query.get_or_404(id)
    db.session.delete(threat)
    db.session.commit()
    flash('Threat deleted successfully!', 'success')
    return redirect(url_for('threats'))

# Vulnerabilities Routes
@app.route('/vulnerabilities')
def vulnerabilities():
    return render_template('vulnerabilities.html', vulnerabilities=Vulnerability.query.all())

@app.route('/vulnerabilities/new')
def new_vulnerability():
    return render_template('vulnerability_form.html', vulnerability=None)

@app.route('/vulnerabilities', methods=['POST'])
def create_vulnerability():
    vulnerability = Vulnerability(
        name=request.form['name'],
        cve_id=request.form['cve_id'],
        severity=request.form['severity'],
        description=request.form['description']
    )
    db.session.add(vulnerability)
    db.session.commit()
    flash('Vulnerability created successfully!', 'success')
    return redirect(url_for('vulnerabilities'))

@app.route('/vulnerabilities/<int:id>/edit')
def edit_vulnerability(id):
    return render_template('vulnerability_form.html', vulnerability=Vulnerability.query.get_or_404(id))

@app.route('/vulnerabilities/<int:id>/update', methods=['POST'])
def update_vulnerability(id):
    vulnerability = Vulnerability.query.get_or_404(id)
    vulnerability.name = request.form['name']
    vulnerability.cve_id = request.form['cve_id']
    vulnerability.severity = request.form['severity']
    vulnerability.description = request.form['description']
    db.session.commit()
    flash('Vulnerability updated successfully!', 'success')
    return redirect(url_for('vulnerabilities'))

@app.route('/vulnerabilities/<int:id>/delete', methods=['POST'])
def delete_vulnerability(id):
    vulnerability = Vulnerability.query.get_or_404(id)
    db.session.delete(vulnerability)
    db.session.commit()
    flash('Vulnerability deleted successfully!', 'success')
    return redirect(url_for('vulnerabilities'))

@app.route('/api/risks')
def api_risks():
    risks = Risk.query.all()
    result = []
    for r in risks:
        result.append({
            'id': r.id,
            'risk_name': r.risk_name,
            'asset': r.asset.name,
            'threat': r.threat.name,
            'vulnerability': r.vulnerability.name,
            'likelihood': r.likelihood,
            'impact': r.impact,
            'risk_score': r.risk_score,
            'risk_level': r.risk_level,
            'owner': r.owner,
            'status': r.status,
            'mitigation': r.mitigation
        })
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
