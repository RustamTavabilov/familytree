from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from .models import Profile, Relationship
from .forms import ProfileForm, RelationshipForm


def home(request):
    return render(request, 'tree/home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                first_name="",
                last_name="",
                created_by=user,
                generation=0
            )
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('profile_view')
    else:
        form = UserCreationForm()
    return render(request, 'tree/register.html', {'form': form})


#############################################
# РАБОТА С АНКЕТАМИ
#############################################

@login_required
def profile_edit(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(
            user=request.user,
            first_name="",
            last_name="",
            created_by=request.user,
            generation=0
        )

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Анкета успешно обновлена!')
            return redirect('profile_view')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'tree/profile_edit.html', {
        'form': form,
        'profile': profile
    })


@login_required
def profile_view(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(
            user=request.user,
            first_name="",
            last_name="",
            created_by=request.user,
            generation=0
        )
    return render(request, 'tree/profile_view.html', {'profile': profile})


@login_required
def profiles_list(request):
    profiles = Profile.objects.filter(created_by=request.user).exclude(user=request.user)
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        user_profile = None

    return render(request, 'tree/profiles_list.html', {
        'profiles': profiles,
        'user_profile': user_profile
    })


@login_required
def profile_create(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.created_by = request.user
            profile.generation = 0
            profile.save()
            messages.success(request, f'Анкета {profile.get_full_name()} успешно создана!')
            return redirect('profiles_list')
    else:
        form = ProfileForm()
    return render(request, 'tree/profile_create.html', {'form': form})


@login_required
def profile_update(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    if profile.created_by != request.user:
        messages.error(request, 'У вас нет прав для редактирования этой анкеты.')
        return redirect('profiles_list')

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Анкета {profile.get_full_name()} обновлена!')
            return redirect('profiles_list')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'tree/profile_update.html', {
        'form': form,
        'profile': profile
    })


@login_required
def profile_delete(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    if profile.user == request.user:
        messages.error(request, 'Нельзя удалить свою собственную анкету!')
        return redirect('profiles_list')

    if profile.created_by == request.user:
        Relationship.objects.filter(
            Q(person_from=profile) | Q(person_to=profile)
        ).delete()
        name = profile.get_full_name()
        profile.delete()
        messages.success(request, f'Анкета {name} удалена.')

    return redirect('profiles_list')


#############################################
# РАБОТА СО СВЯЗЯМИ
#############################################

@login_required
def relationships_list(request):
    relationships = Relationship.objects.filter(
        Q(person_from__created_by=request.user) |
        Q(person_to__created_by=request.user)
    ).distinct()

    return render(request, 'tree/relationships_list.html', {
        'relationships': relationships
    })


def recalculate_generations(start_profile):
    """
    Пересчитывает поколения для всех связанных профилей
    Используется при создании связи между двумя деревьями
    """
    visited = set()
    queue = [(start_profile, start_profile.generation)]

    while queue:
        profile, gen = queue.pop(0)
        if profile.id in visited:
            continue

        visited.add(profile.id)
        old_gen = profile.generation
        profile.generation = gen
        profile.save()

        # Находим всех связанных
        relationships = Relationship.objects.filter(
            Q(person_from=profile) | Q(person_to=profile)
        ).select_related('person_from', 'person_to')

        for rel in relationships:
            if rel.person_from.id == profile.id:
                # Я - from, смотрю на to
                if rel.relationship_type in ['son', 'daughter']:
                    # Я родитель, ребенок младше на 1
                    queue.append((rel.person_to, gen + 1))
                elif rel.relationship_type in ['mother', 'father']:
                    # Я ребенок, родитель старше на 1
                    queue.append((rel.person_to, gen - 1))
                elif rel.relationship_type in ['husband', 'wife']:
                    # Супруг на том же уровне
                    queue.append((rel.person_to, gen))

            if rel.person_to.id == profile.id:
                # Я - to, смотрю на from
                if rel.relationship_type in ['son', 'daughter']:
                    # Я ребенок, родитель старше на 1
                    queue.append((rel.person_from, gen - 1))
                elif rel.relationship_type in ['mother', 'father']:
                    # Я родитель, ребенок младше на 1
                    queue.append((rel.person_from, gen + 1))
                elif rel.relationship_type in ['husband', 'wife']:
                    # Супруг на том же уровне
                    queue.append((rel.person_from, gen))

    return visited


@login_required
def relationship_create(request):
    if request.method == 'POST':
        form = RelationshipForm(request.POST)
        if form.is_valid():
            relationship = form.save(commit=False)
            relationship.created_by = request.user

            # Получаем анкеты
            person_from = relationship.person_from
            person_to = relationship.person_to
            rel_type = relationship.relationship_type

            # Проверяем, связаны ли уже эти люди
            existing = Relationship.objects.filter(
                Q(person_from=person_from, person_to=person_to) |
                Q(person_from=person_to, person_to=person_from)
            ).exists()

            if existing:
                messages.warning(request, 'Эти люди уже связаны!')
                return redirect('relationships_list')

            # Сохраняем связь
            relationship.save()

            # ============= ПЕРЕСЧЕТ ПОКОЛЕНИЙ =============
            # Определяем, какое поколение должно быть у person_to

            if rel_type in ['son', 'daughter']:
                # person_from - родитель, person_to - ребенок
                target_gen = person_from.generation + 1
            elif rel_type in ['mother', 'father']:
                # person_from - ребенок, person_to - родитель
                target_gen = person_from.generation - 1
            elif rel_type in ['husband', 'wife']:
                # Супруги - одинаковый уровень
                target_gen = person_from.generation

            # Если у person_to поколение не совпадает с нужным
            if person_to.generation != target_gen:
                print(f"\n🔄 ОБЪЕДИНЕНИЕ ДЕРЕВЬЕВ:")
                print(f"  {person_from.get_full_name()} (поколение {person_from.generation})")
                print(f"  {rel_type} -> {person_to.get_full_name()} (поколение {person_to.generation})")
                print(f"  Нужное поколение: {target_gen}")

                # Запоминаем старое поколение для отладки
                old_gen = person_to.generation

                # Меняем поколение person_to
                person_to.generation = target_gen
                person_to.save()

                # Пересчитываем всех, кто связан с person_to
                recalculate_generations(person_to)

                print(f"  ✅ Деревья объединены!")

            messages.success(request, 'Связь успешно создана!')
            return redirect('relationships_list')
    else:
        form = RelationshipForm()
        form.fields['person_from'].queryset = Profile.objects.filter(created_by=request.user)
        form.fields['person_to'].queryset = Profile.objects.filter(created_by=request.user)

    return render(request, 'tree/relationship_create.html', {'form': form})


@login_required
def relationship_delete(request, relationship_id):
    relationship = get_object_or_404(Relationship, id=relationship_id)

    if relationship.created_by == request.user:
        relationship.delete()
        messages.success(request, 'Связь удалена.')

    return redirect('relationships_list')


#############################################
# ВИЗУАЛИЗАЦИЯ
#############################################

@login_required
def get_tree_data(request, root_id=None):
    """
    Показываем все анкеты с их поколениями
    """
    try:
        user_profile = Profile.objects.get(user=request.user)

        # Все анкеты пользователя
        all_profiles = Profile.objects.filter(created_by=request.user)
        profiles_data = []
        profile_map = {}

        for profile in all_profiles:
            profile_data = {
                'id': profile.id,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'patronymic': profile.patronymic,
                'full_name': profile.get_full_name(),
                'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                'birth_year': profile.birth_date.year if profile.birth_date else None,
                'is_current_user': profile.user == request.user,
                'gender': 'female' if profile.first_name and profile.first_name.endswith('а') else 'male',
                'generation': profile.generation
            }
            profiles_data.append(profile_data)
            profile_map[profile.id] = profile_data

        # Все связи
        relationships = Relationship.objects.filter(
            person_from__created_by=request.user,
            person_to__created_by=request.user
        )

        relationships_data = []
        for rel in relationships:
            relationships_data.append({
                'from_id': rel.person_from.id,
                'to_id': rel.person_to.id,
                'type': rel.relationship_type,
                'type_display': rel.get_relationship_type_display()
            })

        # ============= НАХОДИМ ОТДЕЛЬНЫЕ ДЕРЕВЬЯ =============
        # Строим граф связей
        graph = {}
        for rel in relationships_data:
            if rel['from_id'] not in graph:
                graph[rel['from_id']] = []
            if rel['to_id'] not in graph:
                graph[rel['to_id']] = []
            graph[rel['from_id']].append(rel['to_id'])
            graph[rel['to_id']].append(rel['from_id'])

        # Находим компоненты связности (отдельные деревья)
        visited = set()
        trees = []

        for profile in profiles_data:
            if profile['id'] not in visited:
                # Новое дерево
                tree = []
                queue = [profile['id']]

                while queue:
                    node = queue.pop(0)
                    if node in visited:
                        continue
                    visited.add(node)
                    tree.append(node)

                    if node in graph:
                        for neighbor in graph[node]:
                            if neighbor not in visited:
                                queue.append(neighbor)

                trees.append(tree)

        print("\n" + "=" * 70)
        print(f"НАЙДЕНО ДЕРЕВЬЕВ: {len(trees)}")
        print("=" * 70)

        for i, tree in enumerate(trees):
            print(f"\n🌳 ДЕРЕВО {i + 1}:")
            for profile_id in tree:
                profile = profile_map.get(profile_id, {})
                name = profile.get('full_name', 'Unknown')
                gen = profile.get('generation', 0)
                print(f"  - {name}: поколение {gen}")

        # Находим супругов (по общим детям)
        spouses = []
        children_map = {}
        for rel in relationships_data:
            if rel['type'] in ['son', 'daughter']:
                parent_id = rel['from_id']
                child_id = rel['to_id']
                if child_id not in children_map:
                    children_map[child_id] = []
                children_map[child_id].append(parent_id)

        for child_id, parents in children_map.items():
            if len(parents) == 2:
                pair = tuple(sorted(parents))
                if pair not in spouses:
                    spouses.append(pair)

        data = {
            'profiles': profiles_data,
            'relationships': relationships_data,
            'root_id': user_profile.id,
            'root_name': user_profile.get_full_name(),
            'current_user_id': user_profile.id,
            'generations': {p['id']: p['generation'] for p in profiles_data},
            'spouses': spouses,
            'trees': trees  # Отправляем информацию о деревьях
        }

        return JsonResponse(data)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def tree_visualization(request):
    return render(request, 'tree/tree_viz.html')