from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import main_bp
from app.models.categoria import Categoria
from app.forms.categoria_forms import CategoriaForm
from app import db

@main_bp.route('/categorias', methods=['GET'])
@login_required
def listar_categorias():
    categorias = Categoria.query.all()
    return render_template('categorias/listar.html', categorias=categorias)

@main_bp.route('/categorias/novo', methods=['GET', 'POST'])
@login_required
def criar_categoria():
    form = CategoriaForm()
    if form.validate_on_submit():
        nova_categoria = Categoria(
            titulo_categoria=form.titulo_categoria.data,
            descricao_categoria=form.descricao_categoria.data,
            is_ativo=form.is_ativo.data
        )
        
        db.session.add(nova_categoria)
        db.session.commit()
        
        flash('Categoria criada com sucesso!', 'success')
        return redirect(url_for('main.listar_categorias'))
    
    return render_template('categorias/novo.html', form=form)

@main_bp.route('/categorias/editar/<int:id_categoria>', methods=['GET', 'POST'])
@login_required
def editar_categoria(id_categoria):
    categoria = Categoria.query.get_or_404(id_categoria)
    form = CategoriaForm(categoria_id=id_categoria)
    
    if form.validate_on_submit():
        categoria.titulo_categoria = form.titulo_categoria.data
        categoria.descricao_categoria = form.descricao_categoria.data
        categoria.is_ativo = form.is_ativo.data
        
        db.session.commit()
        
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_categorias'))
    
    # Preenche o formulário com os dados atuais da categoria
    form.titulo_categoria.data = categoria.titulo_categoria
    form.descricao_categoria.data = categoria.descricao_categoria
    form.is_ativo.data = categoria.is_ativo
    
    return render_template('categorias/editar.html', form=form, categoria=categoria)

@main_bp.route('/categorias/desativar/<int:id_categoria>', methods=['GET'])
@login_required
def desativar_categoria(id_categoria):
    categoria = Categoria.query.get_or_404(id_categoria)
    
    # Desativa a categoria
    categoria.is_ativo = False
    db.session.commit()
    
    flash('Categoria desativada com sucesso!', 'success')
    return redirect(url_for('main.listar_categorias'))
