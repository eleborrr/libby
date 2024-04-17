function add_book_tag(json_) {
    var path;
    if (json_["photo_path"].includes('None'))
        path = '/static/img/no_edition_image.png'
    else
        path = json_["photo_path"]
    let tag_str = `<div>
                        <p>${json_["name"]}</p>
                        <p>${json_["author"]}</p>
                        <p>${json_["publication_year"]}</p>
                        <img src="${path}" alt="${json_["name"]}"
                   </div>`
    let board = document.getElementsByTagName('body')[0]; // Поменять после изменения my_books.html
    let button = document.getElementById('next-page');
    board.removeChild(button);
    board.innerHTML += '\n';
    board.innerHTML += tag_str;
    board.appendChild(button);
}

function _main(page, cur_us_id) {
    fetch(`/get_page_of/2/${page}?owner_id=${cur_us_id}`).then((response) => {
        let page_size = 50;  // Должен совпадать с PAGE_SIZE в consts.py
        response.json().then((data) => {
            console.log(data, 'halo')
            console.log(data['els'].length)
            let board = document.getElementsByTagName("body")[0]; // Поменять после изменения my_books.html
            let button = document.getElementById('next-page');
            if (data['els'].length === 0) {
                console.log('aga')
                // board.removeChild(button);
                try {
                    board.removeChild(button);
                } catch (err) {
                }
            }
            else
                for (var i in data["els"])
                    if (i != data["els"].length - 1 || data['els'].length <= page_size)
                        add_book_tag(data['els'][i]['edition'])
            if (data['els'].length <= page_size && data['els'].length != 0) {
                board.removeChild(button);
            }
        })
    })
}

function main(page) {
    fetch('/cur_us_id').then((response) => {
        response.json().then((data) => _main(page, data['id']))
    })
}

let page = 1;

function next_onclick() {
    main(page);
    page++;
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
    let spinner = document.getElementById('next-page');
    if (!spinner)
        return;
    if (is_visible(spinner))
        next_onclick();
})

next_onclick();