package com.study;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.TreeMap;

public class MapExample1 {

	public static void main(String args[]){
		int[] array = {12,2,15,8,13,76,2,56};
		Set<Integer> duplicat = new HashSet<Integer>(); 
		for (int value:array)
		{
			System.out.println(duplicat.add(value) + " : value : "+value);
		}
		Map<String, String> map = new HashMap<String, String>();
		String a = map.put("aa", "value1");
		String b = map.put("aaa", "value2");
		
		Set<Entry<String, String>> it = map.entrySet();
		Iterator<Entry<String, String>> it1 = it.iterator();
		while (it1.hasNext()) {
			System.out.println(it1.next());
			
		}
		System.out.println(a);
		System.out.println(b);
		
		
		Collection<String> values = map.values();
		Iterator<String> collectionIterator = values.iterator();
		while(collectionIterator.hasNext()){
			System.out.println(collectionIterator.next());
			System.out.println(collectionIterator.next());
			collectionIterator.remove();
		}
		
		/*values.remove("value2");
		values.add("test");*/
		Set<Entry<String, String>> againIterate = map.entrySet();
		Iterator<Entry<String, String>> againIterateIt1 = it.iterator();
		while (againIterateIt1.hasNext()) {
			System.out.println(againIterateIt1.next());
			
		}
		
		Map<String, String> treeMap = new TreeMap<String, String>();
		treeMap.put("aa", "v1");
		Collections.sort(new ArrayList<String>());
	}
}
