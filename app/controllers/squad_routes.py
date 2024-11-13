from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import main_bp
from app.models.squad import Squad
from app.forms.squad_forms import SquadForm
from app import db

@main_bp.route('/squads', methods=['GET'])
@login_required
def listar_squads():
    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    squads = Squad.query.all()
    return render_template('squads/listar.html', squads=squads)

@main_bp.route('/squads/novo', methods=['GET', 'POST'])
@login_required
def criar_squad():
    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    form = SquadForm()
    if form.validate_on_submit():
        novo_squad = Squad(
            titulo_squad=form.titulo_squad.data,
            is_ativo=form.is_ativo.data
        )
        
        db.session.add(novo_squad)
        db.session.commit()
        
        flash('Squad criado com sucesso!', 'success')
        return redirect(url_for('main.listar_squads'))
    
    return render_template('squads/novo.html', form=form)

@main_bp.route('/squads/editar/<int:id_squad>', methods=['GET', 'POST'])
@login_required
def editar_squad(id_squad):
    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    squad = Squad.query.get_or_404(id_squad)
    form = SquadForm(squad_id=id_squad)
    
    if form.validate_on_submit():
        squad.titulo_squad = form.titulo_squad.data
        squad.is_ativo = form.is_ativo.data
        
        db.session.commit()
        
        flash('Squad atualizado com sucesso!', 'success')
        return redirect(url_for('main.listar_squads'))
    
    # Preenche o formulário com os dados atuais do squad
    form.titulo_squad.data = squad.titulo_squad
    form.is_ativo.data = squad.is_ativo
    
    return render_template('squads/editar.html', form=form, squad=squad)

@main_bp.route('/squads/desativar/<int:id_squad>', methods=['GET'])
@login_required
def desativar_squad(id_squad):
    if not current_user.is_administrador:
        flash('Acesso não autorizado', 'danger')
        return redirect(url_for('main.home'))
    
    squad = Squad.query.get_or_404(id_squad)
    
    # Desativa o squad
    squad.is_ativo = False
    db.session.commit()
    
    flash('Squad desativado com sucesso!', 'success')
    return redirect(url_for('main.listar_squads'))
