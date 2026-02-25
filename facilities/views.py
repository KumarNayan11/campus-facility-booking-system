from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required


def facility_list(request):
    return render(request, 'facilities/list.html')


def facility_detail(request, pk):
    return render(request, 'facilities/detail.html', {'pk': pk})


@login_required
def facility_create(request):
    return render(request, 'facilities/form.html')


@login_required
def facility_edit(request, pk):
    return render(request, 'facilities/form.html', {'pk': pk})


@login_required
def facility_delete(request, pk):
    return redirect('facilities:list')
