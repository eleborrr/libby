from abc import abstractmethod, ABC
from libby.consts import *


class CodeGenerator(ABC):
    def generate(self):
        res = f"""function add_tag(json_){{
        let tag_str = `{self.tag_template()}`;
        {self.additional_tag_expression()}
        let board = document.getElementsByClassName("{self.board_class_name()}")[0];
        let sc = document.getElementsByClassName("{self.scroller_div_name()}")[0];
        let button = document.getElementById('next-page');
        sc.removeChild(button);
        board.innerHTML += '\\n';
        board.innerHTML += tag_str;
        sc.appendChild(button);
        }}
        
        function main(page) {{
        do_load = false;
        {self.args_expression()};
            if (!args) {{
        args = ''
    }}
        fetch(`/get_page_of/{self.get_mode()}/${{page}}?${{args}}`).then((response) => {{
            let page_size = {PAGE_SIZE};
            response.json().then((data) => {{
                let board = document.getElementsByClassName("{self.scroller_div_name()}")[0];
                let button = document.getElementById('next-page');
                if (data['els'].length == 0) {{
                    try {{
                        board.removeChild(button);
                    }}
                    catch (err) {{}}
                }} else {{
                    for (let i in data['els']) {{
                        if (i != data['els'].length - 1 || data['els'].length <= page_size) {{
                            add_tag(data['els'][i]);
                        }}
                    }}
                }}
                if (data['els'].length < page_size && data['els'].length != 0)  {{
                    try {{
                        board.removeChild(button);
                    }}
                    catch (err) {{}}
                }}
                do_load = true;
            }})
        }})
        }}
        
        let page = 1;
        let cur_id = null;
        let do_load = true;
        
        function next_onclick() {{
        main(page);
        page++;
        }}
        
        $(window).scroll(function(){{
            if($(window).scrollTop() + $(window).height() > $(document).height()- 20)  {{
                next_onclick();
            }}
        }})

    fetch(`/cur_us_id`).then((response) => {{
            response.json().then((data) => {{
                cur_id = data['id'];
                next_onclick();
            }})
        }}
    )
    {self.in_time_lazy_load()}
        """
        return res

    @abstractmethod
    def tag_template(self):
        pass

    @abstractmethod
    def board_class_name(self):
        pass

    @abstractmethod
    def args_expression(self):
        pass

    @abstractmethod
    def get_mode(self):
        pass

    @abstractmethod
    def scroller_div_name(self):
        pass

    def additional_tag_expression(self):
        return ""

    def in_time_lazy_load(self):
        return ''


class CodeGeneratorWithFilter(CodeGenerator):
    def in_time_lazy_load(self):
        endl = "\n"
        res = f"""
        function button_onclick() {{
            let args="";
            let mp = new Map();
            {endl.join([f'let field{i} = document.querySelector("#{val}");' for i, val in enumerate(self.fields())])}
            
            {endl.join([f'if (field{i}.value) {{{endl}args += `{val}=${{field{i}.value}}`{endl}mp.set("{val}", field{i}.value)}}' for i, val in enumerate(self.fields())])}
            let board = document.getElementsByClassName("{self.board_class_name()}")[0];
            let ch = [];
            for (let i = 0; i < board.children.length;i++) {{
                ch.push(board.children[i]);
            }}
            let l = ch.length;
            for (let i = 0; i < l; i++) {{
                let el = ch[i];
                console.log(el);
                if (el.tagName === "DIV" && el.className === "{self.element_class()}") {{
                    board.removeChild(el);
                }}
            }}
            page = 1;
            let do_load = true;
            
            let button = document.getElementById("next-page");
            if (!button) {{
                let but_div = document.getElementsByClassName("{self.scroller_div_name()}")[0];
                but_div.innerHTML += `<p id="next-page">Ждемс...</p>`
            }}
            window.history.pushState("object", "Title", `${{document.location.href.split("?")[0]}}?${{args}}`);
            
            setTimeout(function () {{
                let v;
                {endl.join([f'v = mp.get("{val}");if (v) {{ document.querySelector("#{val}").value = String(v); }}' for i, val in enumerate(self.fields())])}
            }}, 50)
            next_onclick();}}
        """
        return res

    @abstractmethod
    def fields(self):
        pass

    @abstractmethod
    def element_class(self):
        pass


class EditionsCodeGenerator(CodeGeneratorWithFilter):
    def tag_template(self):
        return """<div class="external">
    <div class="id">
                        </div>
                    <div class="info-border">
                        
                        <div class="info">
                            <p class="text"><a class="table-name">Название</a>: ${json_["name"]}</p>
                            <p class="text"><a class="table-name">Автор</a>: ${json_["author"]}</p>
                            <p class="text"><a class="table-name">Год публикации</a>: ${json_["publication_year"]}</p>
                            <a class="text" href="/library/editions/${json_["id_"]}">Подробнее</a>
                        </div>
                    </div>
                </div>"""

    def board_class_name(self):
        return "flex-second"

    def args_expression(self):
        return """;
        let args = document.location.href.split('?')[1];"""

    def get_mode(self):
        return TARGET_EDITION

    def scroller_div_name(self):
        return "flex-second"

    def fields(self):
        return ["id_", "name", "author", "publication_year"]

    def element_class(self):
        return "external"


class EditionCodeGenerator(CodeGenerator):
    def tag_template(self):
        return """<div class="book-item" style="float: left">
                <div class="img-book bookitem">
                    <p>НЕТ ФОТОЧКАМ!</p>
                </div>
                <div class="descrs bookitem">
                    <h3 style="font-size: 15px">id: ${json_["id_"]}</h3>
"""

    def board_class_name(self):
        return 'ed-books'

    def args_expression(self):
        return """let args = document.location.href.split('?')[1];"""

    def get_mode(self):
        return TARGET_BOOK

    def scroller_div_name(self):
        return 'sc'

    def additional_tag_expression(self):
        return """if (json_["owner_id"])
        if (cur_us_id === 2)
            tag_str += `<a href='/library/books/${json_["id_"]}' class="link-del">Владелец: ${json_["owner_surname"]}</a>`
        else
            tag_str += `<a href='/library/books/${json_["id_"]}' class="link-del">Книга занята</a>`
    else
        tag_str += `<a href='/library/books/${json_["id_"]}' class="link-del green">Книга свободна</a>`
    tag_str += "</div></div>"
    """


class StudentsCodeGenerator(CodeGenerator):
    def tag_template(self):
        return """<div class="izd-item" style="padding: 5px">
    <span style="background-color: #98D9E8;margin-left: 0">${json_["id_"]}</span>
    <a href="/library/profile/${json_["id_"]}">${json_["surname"]} ${json_["name"]}</a>
    <a class='link-izd' href='/library/delete_student/${json_["id_"]}'>Удалить</a>
</div>"""

    def scroller_div_name(self):
        return 'flex-second'

    def board_class_name(self):
        return 'flex-second'

    def get_mode(self):
        return TARGET_STUDENT

    def args_expression(self):
        return """let args = document.location.href.split('?')[1];"""


if __name__ == '__main__':
    with open('testt.js', 'w') as f:
        f.write(EditionsCodeGenerator().generate())
