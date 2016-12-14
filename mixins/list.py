from braces.views import AjaxResponseMixin, JSONResponseMixin
from braces.views._access import AccessMixin
from django.urls import reverse_lazy
from django.utils import six
from django.views.generic import ListView
from django.views.generic.list import BaseListView
from awesome_mixins.utils.geral import parse_date
from django.utils.safestring import mark_safe


def get_order_filter(data=None):
    if data:
        if data == 'asc':
            return 'desc'
        else:
            return 'asc'
    return None


class ListMixin(ListView, AccessMixin, BaseListView, AjaxResponseMixin, JSONResponseMixin):
    """
    Mixin para view de lista
    """
    json_list_name = None
    order_tags = None
    search_default = None
    _active_tag = None
    add_btn = True
    default_order = None

    def get_queryset(self):
        # import pdb; pdb.set_trace()
        # Verificando se o queryset ja esta definido
        if self.queryset is not None or (self.queryset is None and self.model is None):
            # import pdb; pdb.set_trace()
            queryset = super(ListMixin, self).get_queryset()
        else:
            queryset = self.model._default_manager.all()

        # pegando a ordenação padão do model utilizado
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        # se existir tags de ordenação de verifica qual esta vindo na
        # requisição para retornar a mesma filtrada e ordenada
        if self.order_tags:
            found = False
            for line in self.order_tags:
                tag = line[0]
                lookup = line[1]
                if self.request.GET.get(tag, None):
                    found = True
                    prop = tag.replace('_order', '')
                    # import pdb; pdb.set_trace()
                    if self.request.GET.get(prop, None):
                        term = self.request.GET.get(prop, None)
                        date = parse_date(term)
                        if date:
                            queryset = queryset.filter(**{lookup: date})
                        else:
                            if '|' in term:
                                queryset = queryset.filter(**{lookup + '__icontains': term.replace('|', '')})
                            else:
                                queryset = queryset.filter(**{lookup + '__istartswith': term})
                    order = self.request.GET.get(tag, 'asc')
                    order = lookup if order == 'asc' else '-' + lookup
                    queryset = queryset.order_by(order)
                    break

            if not found:
                if self.request.GET.get(self.search_default[0], None):
                    term = self.request.GET.get(self.search_default[0], None)
                    date = parse_date(term)
                    if date:
                        queryset = queryset.filter(**{self.search_default[1]: date})
                    else:
                        if '|' in term:
                            queryset = queryset.filter(
                                **{self.search_default[1] + '__icontains': term.replace('|', '')})
                        else:
                            queryset = queryset.filter(**{self.search_default[1] + '__istartswith': term})

                if self.default_order:
                    queryset = queryset.order_by(self.default_order)
                else:
                    queryset = queryset.order_by(self.search_default[1])

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ListMixin, self).get_context_data(**kwargs)

        if self.order_tags:
            for tag in self.order_tags:
                t = get_order_filter(self.request.GET.get(tag[0], None))
                context[tag[0]] = t
                if t:
                    self._active_tag = tag

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax():
            return self.get_ajax(self.request, **context)
        return super(ListMixin, self).render_to_response(context, **response_kwargs)

    def get_ajax(self, request, *args, **kwargs):
        json_dict = {self.json_list_name: [obj.serialize() for obj in kwargs['object_list']]}
        paginador = kwargs['paginator'] if 'paginator' in kwargs else None
        num_pages = 1
        if paginador:
            num_pages = paginador.num_pages if paginador.num_pages > 0 else 1

        json_dict['num_pages'] = num_pages
        return self.render_json_response(json_dict)

    def as_table(self):
        output = []
        output.append(self._header())
        output.append(self._body())
        output.append(self._footer())
        return mark_safe('\n'.join(output))

    def _header(self):
        fdiv = '</div>'
        output = []
        if self.order_tags:
            output.append('<div class="box-header">')
            output.append('<div class="row">')

            # Busca
            if self.add_btn:
                output.append('<div class="col-xs-6">')
            else:
                output.append('<div class="col-xs-12 col-sm-6 col-md-6">')
            output.append('<div class="input-group input-group-sm">')

            string_search = '<input id="busca" type="text" class="form-control" placeholder="Busca por {placeholder}" style="height: 38px;">'
            if self._active_tag:
                string_search = string_search.format(placeholder=self._active_tag[2])
            else:
                string_search = string_search.format(placeholder=self.search_default[2])

            output.append(string_search)
            output.append('<span class="input-group-btn">')
            output.append('<button type="button" onclick="Busca()" class="btn btn-default" style="height: 38px;"><i class="fa fa-search"></i></button>')
            output.append('</span>')
            output.append(fdiv)
            output.append(fdiv)

            # meio
            # output.append('<div class="col-xs-2">')
            # output.append(fdiv)

            # Botão de adicionar
            if self.add_btn:
                output.append('<div class="col-xs-6">')
                url = reverse_lazy(self.model.__name__.lower() + '-create')
                output.append("""<a id="adicionar-button" class="btn btn-flat btn-lg btn-primary
                 pull-right"

                 href="{url}"><i class="fa fa-plus"></i> Criar Pedido</a>""".format(url=url))
                output.append(fdiv)

            output.append(fdiv)
            output.append(fdiv)
        return ''.join(output)

    def _body(self):
        fdiv = '</div>'
        output = []
        if self.order_tags:
            context = self.get_context_data()
            arrow_up = '<i class="fa fa-arrow-up" style="color: red"></i>'
            arrow_down = '<i class="fa fa-arrow-down" style="color: limegreen"></i>'
            normal_row = """<th {width}><a href="?{tag}={ordering}">{name} {arrow}</a></th>"""

            output.append('<div class="box-body table-responsive no-padding">')
            table_id = self.model.__name__.lower() + '_table'
            output.append('<table id="{id}" class="table table-bordered table-condensed table-hover">'.format(id=table_id))

            output.append('<thead>')
            output.append('<tr>')
            for tp in self.order_tags:
                if len(tp) == 3:
                    tag, lookup, name = tp
                    width = ''
                else:
                    tag, lookup, name, width = tp
                    width = 'width={w}'.format(w=width)
                ordering = context[tag] if context[tag] else 'asc'
                arrow = ''
                if context[tag]:
                    arrow = arrow_up if ordering == 'asc' else arrow_down
                output.append(normal_row.format(tag=tag, ordering=ordering, name=name, arrow=arrow, width=width))
            output.append('</tr>')
            output.append('</thead>')

            output.append('<tbody>')
            output.append('</tbody>')

            output.append('</table>')
            output.append(fdiv)

        return ''.join(output)

    def _footer(self):
        output = []
        output.append('<div class="box-footer clearfix">')
        output.append('<ul id="pagination">')
        output.append('</ul>')
        output.append('</div>')
        return ''.join(output)

    def get_json_list_name(self):
        return self.json_list_name

    def get_search_default(self):
        return self.search_default
