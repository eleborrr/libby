function add_edition_tag(json_) {
    var path;
    if (json_["photo_path"].includes('None'))
        path = '/static/img/no_edition_image.png'
    else
        path = json_["photo_path"]

    let tag_str = `<div class="external">
    <div class="id">
                            <img class="image-img" src="${path}" alt="${json_["name"]}" onclick="document.location.href = '/library/add_edition_photo/${json_["id_"]}'">
                        </div>
                    <div class="info-border">
                        
                        <div class="info">
                            <p class="text"><a class="table-name">Название</a>: ${json_["name"]}</p>
                            <p class="text"><a class="table-name">Автор</a>: ${json_["author"]}</p>
                            <p class="text"><a class="table-name">Год публикации</a>: ${json_["publication_year"]}</p>
                            <a class="text" href="/library/editions/${json_["id_"]}">Подробнее</a>
                        </div>
                    </div>
                </div>`

    let board = document.getElementsByClassName("flex-second")[0];
    let button = document.getElementById('next-page');
    board.removeChild(button);
    board.innerHTML += '\n';
    board.innerHTML += tag_str;
    board.appendChild(button);
}

function add_student_tag(json_) {
    let tag_str = `
<div class="izd-item" style="padding: 5px">
    <span style="background-color: #98D9E8;margin-left: 0">${json_["id_"]}</span>
    <a href="/library/profile/${json_["id_"]}">${json_["surname"]} ${json_["name"]}</a>
    <a class='link-izd' href='/library/delete_student/${json_["id_"]}'>Удалить</a>
</div>`
    let board = document.getElementsByClassName("flex-second")[0];
    let button = document.getElementById('next-page');
    board.removeChild(button);
    board.innerHTML += '\n';
    board.innerHTML += tag_str;
    board.appendChild(button);
}

function _add_book_tag(json_, cur_us_id) {
    let tag_str = `<div class="book-item" style="float: left">
                <div class="img-book bookitem">
                    <p>НЕТ ФОТОЧКАМ!</p>
                </div>
                <div class="descrs bookitem">
                    <h3 style="font-size: 15px">id: ${json_["id_"]}</h3>
`
    if (json_["owner_id"])
        if (cur_us_id === 2)
            tag_str += `<a href='/library/books/${json_["id_"]}' class="link-del">Владелец: ${json_["owner_surname"]}</a>`
        else
            tag_str += `<a href='/library/books/${json_["id_"]}' class="link-del">Книга занята</a>`
    else
        tag_str += `<a href='/library/books/${json_["id_"]}' class="link-del green">Книга свободна</a>`
    tag_str += "</div></div>"
    let board = document.getElementsByClassName("ed-books")[0];
    board.innerHTML += '\n';
    board.innerHTML += tag_str;
}

function add_book_tag(json_) {
    _add_book_tag(json_, cur_id);
    // httpGetAsync('/cur_us_id',
    //     function (data) {
    //         _add_book_tag(json_, JSON.parse(data))
    //     })
}

function get_mode() {
    var knigger = document.location.href.split('?')[0].split('/');
    if (document.location.href.includes('edition'))
        if (knigger[knigger.length - 1] === 'editions')
            return 1
        else
            return 2
    else return 3
}

function main(page) {
    do_load = false;
    var mode = get_mode();
    var f;
    var args = document.location.href.split('?')[1]
    if (!args) {
        args = ''
    }
    if (mode === 2) {
        let attrs = document.location.href.split('?')[0].split('/');
        if (args)
            args += `&edition_id=${attrs[attrs.length - 1]}`
        else
            args += `edition_id=${attrs[attrs.length - 1]}`
    }


    if (mode === 1) {
        f = add_edition_tag;
    } else {
        if (mode === 2) {
            f = add_book_tag;
        } else {
            f = add_student_tag;
        }
    }
    fetch(`/get_page_of/${mode}/${page}?${args}`).then((response) => {
            let page_size = 50;  // Должен совпадать с PAGE_SIZE в consts.py
            response.json().then((data) => {
                if (data['els'].length === 0) {
                    var board;
                    if (mode === 2)
                        board = document.getElementsByClassName("butt")[0];
                    else
                        board = document.getElementsByClassName("flex-second")[0];
                    let button = document.getElementById('next-page');
                    try {
                        board.removeChild(button);
                    } catch (err) {
                    }
                } else
                    for (let i in data["els"]) {
                        console.log(i, data['els'][i]['id_']);
                        f(data['els'][i]);
                    }
                if (data['els'].length < page_size && data['els'].length != 0) {
                    var board;
                    if (mode === 2)
                        board = document.getElementsByClassName("sc")[0];
                    else
                        board = document.getElementsByClassName("flex-second")[0];
                    let button = document.getElementById('next-page');
                   try {
                        board.removeChild(button);
                    } catch (err) {
                    }
                }
                do_load = true;
            })
        }
    )
    // httpGetAsync(`/get_page_of/${mode}/${page}?${document.location.href.split('?')[1]}`,
    //     function (data){
    //     let json_ = JSON.parse(data);
    //     for (var i in json_["els"])
    //         f(i)
    //     })
}

let page = 1;
let cur_id = null;
let do_load = true;

function next_onclick() {
    main(page);
    page++;
}

function posY(elm) {
    var test = elm, top = 0;

    while (!!test && test.tagName.toLowerCase() !== "body") {
        top += test.offsetTop;
        test = test.offsetParent;
    }

    return top;
}

function viewPortHeight() {
    var de = document.documentElement;

    if (!!window.innerWidth) {
        return window.innerHeight;
    } else if (de && !isNaN(de.clientHeight)) {
        return de.clientHeight;
    }

    return 0;
}

function scrollY() {
    if (window.pageYOffset) {
        return window.pageYOffset;
    }
    return Math.max(document.documentElement.scrollTop, document.body.scrollTop);
}

function checkvisible(elm) {
    var vpH = viewPortHeight(), // Viewport Height
        st = scrollY(), // Scroll Top
        y = posY(elm);

    return (y > (vpH + st));
}

function is_visible(target) {
    var targetPosition = {
            top: window.pageYOffset + target.getBoundingClientRect().top,
            left: window.pageXOffset + target.getBoundingClientRect().left,
            right: window.pageXOffset + target.getBoundingClientRect().right,
            bottom: window.pageYOffset + target.getBoundingClientRect().bottom
        },
        // Получаем позиции окна
        windowPosition = {
            top: window.pageYOffset,
            left: window.pageXOffset,
            right: window.pageXOffset + document.documentElement.clientWidth,
            bottom: window.pageYOffset + document.documentElement.clientHeight
        };
    return (targetPosition.bottom > windowPosition.top && // Если позиция нижней части элемента больше позиции верхней чайти окна, то элемент виден сверху
        targetPosition.top < windowPosition.bottom && // Если позиция верхней части элемента меньше позиции нижней чайти окна, то элемент виден снизу
        targetPosition.right > windowPosition.left && // Если позиция правой стороны элемента больше позиции левой части окна, то элемент виден слева
        targetPosition.left < windowPosition.right)
}

document.addEventListener('scroll', function () {
    if (!do_load) {
        return;
    }
    let spinner = document.getElementById('next-page');
    if (!spinner)
        return;
    if (is_visible(spinner)) {
        next_onclick();
    }
})

    fetch(`/cur_us_id`).then((response) => {
            response.json().then((data) => {
                cur_id = data['id'];
                next_onclick();
            })
        }
    )