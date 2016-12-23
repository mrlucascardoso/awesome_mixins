from braces.views import AjaxResponseMixin, JSONResponseMixin
from braces.views._access import AccessMixin
from django.utils import six
from django.views.generic import ListView
from django.views.generic.list import BaseListView
from awesome_mixins.utils.geral import parse_date
from django.utils.safestring import mark_safe
from django.conf import settings
import inspect


def get_order_filter(data=None):
    if data:
        if data == 'asc':
            return 'desc'
        else:
            return 'asc'
    return None


class ListMixin(ListView, AccessMixin, BaseListView, AjaxResponseMixin, JSONResponseMixin):
    """
    Mixin for list view with saerch and order
    """
    json_list_name = None
    columns = None
    search_default = None
    _active_tag = None
    add_btn = True
    add_button_url = '#'
    add_button_name = 'Add'
    search_placeholder = None
    search_id = None
    table_id = None
    num_pages = None
    css_template = 'admin_lte'
    css_table = None
    css_div_header = None
    css_div_body = None
    css_div_footer = None
    _translate = {
        'search_placeholder': {
            'en-us': 'Search for',
            'pt-br': 'Busca por'
        }
    }

    def get_queryset(self):
        # Checking if exist defined a queryset
        if self.queryset is not None or (self.queryset is None and self.model is None):
            queryset = super(ListMixin, self).get_queryset()
        else:
            queryset = self.model._default_manager.all()

        # Get default order by model
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        # If there are any sort tags, it checks which one is in a request to return the same filtered and ordered.
        if self.columns:
            found = False
            for line in self.get_columns():
                lookup = line['lookup']
                tag = '{}_order'.format(lookup)
                if self.request.GET.get(tag, None):
                    found = True
                    if self.request.GET.get(lookup, None):
                        term = self.request.GET.get(lookup, None)
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
                        queryset = queryset.filter(**{self.search_default[0]: date})
                    else:
                        if '|' in term:
                            queryset = queryset.filter(
                                **{self.search_default[0] + '__icontains': term.replace('|', '')})
                        else:
                            queryset = queryset.filter(**{self.search_default[0] + '__istartswith': term})

                queryset = queryset.order_by(self.search_default[1])

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ListMixin, self).get_context_data(**kwargs)

        paginador = context['paginator'] if 'paginator' in context else None
        self.num_pages = 1
        if paginador:
            self.num_pages = paginador.num_pages if paginador.num_pages > 0 else 1

        if self.columns:
            for line in self.get_columns():
                t = get_order_filter(self.request.GET.get('{}_order'.format(line['lookup']), None))
                context['{}_order'.format(line['lookup'])] = t
                if t:
                    self._active_tag = line

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax():
            return self.get_ajax(self.request, **context)
        return super(ListMixin, self).render_to_response(context, **response_kwargs)

    def get_ajax(self, request, *args, **kwargs):
        return self.render_json_response({
            self.get_json_list_name(): [self.serialize(obj) for obj in kwargs['object_list']],
            'num_pages': self.num_pages
        })

    def as_table(self):
        return mark_safe('\n'.join([
            self._header(),
            self._body(),
            self._footer()
        ]))

    def _header(self):
        fdiv = '</div>'
        output = []
        if self.columns:
            output.append('<div class="{}">'.format(self.get_css_classes('div_header')))
            output.append('<div class="row">')

            # Search
            if self.add_btn:
                output.append('<div class="col-xs-6">')
            else:
                output.append('<div class="col-xs-12 col-sm-6 col-md-6">')
            output.append('<div class="input-group input-group-sm">')

            string_search = """
            <input id="{search_id}" type="text" class="form-control"
                    placeholder="{string_search} {placeholder}" style="height: 38px;">
            """
            if self._active_tag:
                string_search = string_search.format(
                    placeholder=self._active_tag['name'],
                    string_search=self.get_search_placeholder(),
                    search_id=self.get_search_id()
                )
            else:
                string_search = string_search.format(
                    placeholder=self.search_default[2],
                    string_search=self.get_search_placeholder(),
                    search_id=self.get_search_id()
                )

            output.append(string_search)
            output.append('<span class="input-group-btn">')
            output.append("""
                <button type="button" onclick="AmSearch()" class="btn btn-default" style="height: 38px;">
                    <i class="glyphicon glyphicon-search"></i>
                </button>
            """)
            output.append('</span>')
            output.append(fdiv)
            output.append(fdiv)

            # Add button
            if self.add_btn:
                output.append('<div class="col-xs-6">')
                output.append("""<a id="am_add_button" class="btn btn-lg btn-primary
                 pull-right"
                 href="{url}"><i class="glyphicon glyphicon-plus"></i>{name_button}</a>""".format(
                    url=self.add_button_url,
                    name_button=self.add_button_name
                ))
                output.append(fdiv)

            output.append(fdiv)
            output.append(fdiv)
        return ''.join(output)

    def _body(self):
        fdiv = '</div>'
        output = []
        if self.columns:
            context = self.get_context_data()
            arrow_up = '<i class="glyphicon glyphicon-arrow-up" style="color: red"></i>'
            arrow_down = '<i class="glyphicon glyphicon-arrow-down" style="color: limegreen"></i>'
            normal_row = """<th {width}><a href="?{tag}={ordering}">{name} {arrow}</a></th>"""

            output.append('<div class="{}">'.format(self.get_css_classes('div_body')))
            table_id = self.get_table_id()
            output.append(
                '<table id="{id}" class="{table_css}">'.format(id=table_id, table_css=self.get_css_classes('table'))
            )

            output.append('<thead>')
            output.append('<tr>')
            for line in self.get_columns():
                lookup = line['lookup']
                name = line['name']
                width = line['width']
                tag = '{}_order'.format(lookup)
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
        output.append('<div class="{}">'.format(self.get_css_classes('div_footer')))
        output.append('<ul id="pagination">')
        output.append('</ul>')
        output.append('</div>')
        return ''.join(output)

    def as_statics(self):
        table_id = self.get_table_id()
        json_list_name = self.get_json_list_name()
        search_id = self.get_search_id()
        add_args = ''.join([', {}'.format(column['lookup']) for column in self.get_columns()])[2:]
        td_columns = ''.join(
            ["<td nowrap><a href=\"#\">'+ (({field} != null) ? {to_js_function} : '') +'</a></td>".format(
                    field=column['lookup'], to_js_function=column['to_js_function']
            ) for column in self.get_columns()]
        )
        update_columns = ''.join([', data[i]["{}"]'.format(column['lookup']) for column in self.get_columns()])[2:]

        filters = ''.join([
            "else if(url.indexOf('&{field}_order') != -1 || url.indexOf('?{field}_order') != -1){{filter = '&{field}=';}}".format(
                field=column['lookup']
            ) for column in self.get_columns()
        ])

        if self._active_tag:
            search_default = self._active_tag['lookup']
        else:
            search_default = self.search_default[0]

        return mark_safe("""
            <link rel="stylesheet" href="/static/awesome_mixins/css/list_view.css">
            <script src="/static/awesome_mixins/js/twbs-pagination/jquery.twbsPagination.min.js"></script>
            <script type="text/javascript">
                function AmAddLine({add_args}){{
                    $("#{table_id} tbody").append(
                        '<tr>{td_columns}</tr>'
                    );
                }}

                function AmClearTable(){{
                    $('#{table_id} tbody tr').each(function(){{
                        $(this).remove();
                    }});
                }}

                function AmUpdateTable(data) {{
                    AmClearTable();
                    for(var i = 0; i < data.length; i++){{
                        AmAddLine({update_columns});
                    }}
                }}

                function AmCleanSearch() {{
                    var url = window.location.href;
                    url = url.replace("#", "");
                    var filter = '';

                    var search = $('#{search_id}').val();

                    if (search != null && search != ''){{
                        if(url.indexOf('_order') == -1){{
                            filter = '?{search_default}=';
                        }}{filters}

                        filter = filter + search;
                    }}

                    return filter;
                }}

                function AmUpdatePage(page) {{
                    var result;
                    var self = $(this),
                    url = AmToPage(page),
                    ajax_req = $.ajax({{
                        url: url,
                        type: "GET",
                        success: function(data, textStatus, algo) {{
                            if(data['{json_list_name}'] != null){{
                                AmUpdateTable(data['{json_list_name}']);
                            }}
                        }},
                        error: function(data, textStatus) {{
                            console.log(data);
                        }}
                    }});
                }}

                function AmToPage(p) {{
                    var url = window.location.href;
                    url = url.replace("#", "");
                    if(url.indexOf('page') == -1 && url.indexOf('?') == -1){{
                        if(AmCleanSearch() != ''){{
                            return url + AmCleanSearch() + "&page=" + p;
                        }}
                        return url + "?page=" + p;
                    }} else if(url.indexOf('page') == -1){{
                        return url + AmCleanSearch() + "&page=" + p;
                    }}else{{
                        var i = url.indexOf('page') + 5;
                        return url.replaceAt(i, "" + p + "");
                    }}
                }}

                function AmSearch() {{
                    var result;
                    var self = $(this);
                    url = window.location.href + AmCleanSearch();
                    ajax_req = $.ajax({{
                        url: url,
                        type: "GET",
                        success: function(data, textStatus, algo) {{
                            if(data['{json_list_name}'] != null){{
                                AmUpdateTable(data['{json_list_name}'])
                                $('#pagination').twbsPagination('destroy');
                                $('#pagination').twbsPagination({{
                                    totalPages: data['num_pages'],
                                    visiblePages: 3,
                                    first: '<<',
                                    prev: '<',
                                    next: '>',
                                    last: '>>',
                                    onPageClick: function (event, page) {{
                                        AmUpdatePage(page);
                                    }}
                                }}  );
                            }}
                        }},
                        error: function(data, textStatus) {{
                            console.log(data);
                        }}
                    }});
                }}

                try{{
                    $(window).load(function () {{
                        $('#pagination').twbsPagination({{
                            totalPages: {num_pages},
                            visiblePages: 3,
                            first: '<<',
                            prev: '<',
                            next: '>',
                            last: '>>',
                            onPageClick: function (event, page) {{
                                AmUpdatePage(page);
                            }}
                        }});
                    }});
                }}catch(err){{
                    $(window).on('load', function () {{
                        $('#pagination').twbsPagination({{
                            totalPages: {num_pages},
                            visiblePages: 3,
                            first: '<<',
                            prev: '<',
                            next: '>',
                            last: '>>',
                            onPageClick: function (event, page) {{
                                AmUpdatePage(page);
                            }}
                        }});
                    }});
                }}
            </script>
        """.format(
            table_id=table_id,
            json_list_name=json_list_name,
            search_id=search_id,
            num_pages=self.num_pages,
            add_args=add_args,
            td_columns=td_columns,
            update_columns=update_columns,
            search_default=search_default,
            filters=filters
        ))

    def get_json_list_name(self):
        if self.json_list_name:
            return self.json_list_name
        return '{}s'.format(self.model.__name__.lower())

    def get_search_default(self):
        return self.search_default

    def get_table_id(self):
        if self.table_id:
            return self.table_id

        return self.model.__name__.lower() + '_table'

    def get_search_placeholder(self):
        if self.search_placeholder:
            return self.search_placeholder

        try:
            value = self.get_translate('search_placeholder', settings.LANGUAGE_CODE)
            return value
        except KeyError:
            pass

        return 'Without support for this language, please set the search_placeholder in ListMixin'

    def get_search_id(self):
        if self.search_id:
            return self.search_id
        return 'am_search'

    def get_columns(self):
        return [
            {
                'lookup': dc['lookup'],
                'name': dc['name'],
                'width': 'width={}'.format(dc['width']) if 'width' in dc else '',
                'js_function': dc['js_function'] if 'js_function' in dc else '',
                'to_js_function': '{}({})'.format(dc['js_function'], dc['lookup']) if 'js_function' in dc else dc['lookup'],
            } for dc in self.columns
        ]

    def serialize(self, obj):
        result = {}
        for line in self.get_columns():
            fields = line['lookup'].split('__')
            if len(fields) > 1:
                fields.reverse()
            att = self.do_serialize(fields, obj)
            result[line['lookup']] = att
        return result

    def do_serialize(self, fields, obj):
        try:
            if len(fields) == 1:
                field = fields.pop()
                obj = getattr(obj, field)
                return obj
            field = fields.pop()
            obj = getattr(obj, field)
            return self.do_serialize(fields, obj)
        except AttributeError:
            return ''

    def get_translate(self, option, value):
        return self._translate[option][value]

    def get_css_classes(self, key=None):
        css_classes = {
            'admin_lte': {
                'table': 'table table-bordered table-condensed table-hover',
                'div_header': 'box-header',
                'div_body': 'box-body table-responsive no-padding',
                'div_footer': 'box-footer clearfix',
            }
        }

        if self.css_template:
            data = css_classes[self.css_template]

            for field, value in [a for a in inspect.getmembers(self) if a[0].startswith('css_') and a[0] != 'css_template']:
                if value:
                    data[field[4:]] = value

            if key:
                return data[key]

            return data
        else:
            data = {
                'table': self.css_table if self.css_table else '',
                'div_header': self.css_div_header if self.css_div_header else '',
                'div_body': self.css_div_body if self.css_div_body else '',
                'div_footer': self.css_div_footer if self.css_div_footer else '',
            }
            if key:
                return data[key]
            return data
