//更新购物车
function updateCart(id,num) {
    param = {
        'id': id,
        'num': num,
    };
    updateTag = true;
    $.get('/cart/edit/',param,function (data) {
        // alert('更新购物车'+data.res);
        if(data.res=='4'){
            updateTag = true;
            $("#show_count").text(data.cart_count);
        }
        else{
            updateTag = false;
            alert(data.error+',请修改数量')
        }
        })
}
//计算小计金额
function each_total_amount() {
    $('.col07').each(function () {
        //先获取每行 小计 前一列即数量  再获取价格，两者相乘，小计这列再显示出来
        count=$(this).prev().find('input').val();
        price=$(this).prev().prev().text();
        each_total=parseFloat(price)*parseInt(count);
        $(this).text(each_total.toFixed(2));
    })
}
//计算总计金额
function total_all() {
    total_count=0;
    total_amount=0;
    $('.cart_list_td').find(':checked').parents('ul').each(function () {
        var count = $(this).find('#num').val();
        var amount = $(this).children('.col07').text();
        var price = $(this).children('.col05').text();
        total_count += parseInt(count);
        total_amount += parseFloat(amount);
    });
    $('#total_amount').text(total_amount.toFixed(2));
    $('#total_num').text(total_count);
    $('#total_num1').text(total_count);
}
//
$(function () {

    //全选取消
    $('#check_all').click(function () {
        state=$(this).prop('checked');
        $(':checkbox:not(#check_all)').prop('checked',state);
        total_all();
    });
    //单个选择
    $(':checkbox:not(#check_all)').click(function () {
        if($(this).prop('checked')){
            if($(':checked').length+1==$(':checkbox').length){
                $('#check_all').prop('checked',true);
            }
        }else{
            $('#check_all').prop('checked',false);
        }
        total_all();
    });

    //数量加
    $('.add').click(function () {
        num=parseInt($(this).next().val());
        $(this).next().val(num+1).blur();
        id=$("#num").attr("good_id");
        updateCart(id,num+1);
        if(updateTag==true){
            each_total_amount();
            total_all();
        }
        else{
            $(this).next().val(num);
        }
    });

    //数量减
    $('.minus').click(function () {
        num=parseInt($(this).prev().val());
        if(num>1) {
            $(this).prev().val(num-1).blur();
        }
        id=$("#num").attr("good_id");
        updateCart(id,num-1);
        each_total_amount();
        total_all();
    });

    //任意修改数量
    $('.num').blur(function () {
        num=parseInt($(this).val());
        if(num<1) {
            num=1;
            $(this).val(num);
        }
        //向数据库发送数据，修改商品数量
        id=$("#num").attr("good_id");
        updateCart(id,num);
        each_total_amount();
        total_all();

    });

    //商品删除
    $('.delete').click(function () {
        state=confirm("您确定要删除吗？");
        if(state){
            id=$("#num").attr("good_id");
            good_ul=$(this).parents('ul');
            param = {'id':id};
            $.get('/cart/delete/',param,function (data) {
                if(data.res='3'){
                    good_ul.remove();
                    $("#show_count").text(data.cart_count);
                    total_all();
                }else{
                    alert(data.error);
                }
            })
        }
    });
    each_total_amount();
    total_all();
});
