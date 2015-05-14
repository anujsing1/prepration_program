package com.barclay;


public class Tree {
	private int value;
	private Tree left;
	private Tree right;
	private static Tree rootNode = null;
	
	public Tree(int value) {
		this.value = value;
	}
	
	/**
	 * @return the value
	 */
	public int getValue() {
		return value;
	}
	/**
	 * @param value the value to set
	 */
	public void setValue(int value) {
		this.value = value;
	}
	/**
	 * @return the left
	 */
	public Tree getLeft() {
		return left;
	}
	/**
	 * @param left the left to set
	 */
	public void setLeft(Tree left) {
		this.left = left;
	}
	/**
	 * @return the right
	 */
	public Tree getRight() {
		return right;
	}
	/**
	 * @param right the right to set
	 */
	public void setRight(Tree right) {
		this.right = right;
	}
	
	static void insertRec(Tree parentNode, Tree newNode){
		if (null == parentNode){
			rootNode = newNode;
		}
		else {
			Boolean left=null;
			while(true){
				if(parentNode.value > newNode.value){
					if (null == parentNode.getLeft()){
						left = true;
						break;
					}
					parentNode = parentNode.getLeft();
				}
				else if(parentNode.value < newNode.value){
					if (null == parentNode.getRight()){
						left = false;
						break;
					}
					parentNode = parentNode.getRight();
				}
				else {
					left = null;
					break;
				}
			}
			if (null == left){
			}
			else if(left)
				parentNode.left = newNode;
			else if(!left)
				parentNode.right = newNode;
		}
	}
	
	static void inorderRecu(Tree parentNode){
		if(parentNode == null){
			return;
		}
		inorderRecu(parentNode.getLeft());
		System.out.print(parentNode.getValue()+", ");
		inorderRecu(parentNode.getRight());
	}
	
	static void preorderRecu(Tree parentNode){
		if(parentNode == null){
			return;
		}
		System.out.print(parentNode.getValue()+", ");
		preorderRecu(parentNode.getLeft());
		preorderRecu(parentNode.getRight());
	}
	
	static void postorderRecu(Tree parentNode){
		if(parentNode == null){
			return;
		}
		postorderRecu(parentNode.getLeft());
		postorderRecu(parentNode.getRight());
		System.out.print(parentNode.getValue()+", ");
	}
	
	static void searchNode(int val){
		if(rootNode == null){
			return;
		}
		Tree newNode = rootNode;
		while(null != newNode){
			if(val == newNode.getValue()){
				System.out.println("Element Found");
				break;
			}
			else if(val <newNode.getValue()){
				newNode = newNode.getLeft();
			}
			else if(val > newNode.getValue()){
				newNode = newNode.getRight();
			}
		}
	}
	
	public static void main(String[] args) {
		Tree n1 = new Tree(10);
		Tree n2 = new Tree(5);
		Tree n3 = new Tree(7);
		Tree n4 = new Tree(1);
		Tree n5 = new Tree(14);
		Tree n6 = new Tree(13);
		Tree n7 = new Tree(17);
		Tree n8 = new Tree(15);
		
		insertRec(rootNode, n1);
		insertRec(rootNode, n2);
		insertRec(rootNode, n3);
		insertRec(rootNode, n4);
		insertRec(rootNode, n5);
		insertRec(rootNode, n6);
		insertRec(rootNode, n7);
		insertRec(rootNode, n8);
		searchNode(12);

		System.out.println();
		inorderRecu(rootNode);
		System.out.println();
		preorderRecu(rootNode);
		System.out.println();
		postorderRecu(rootNode);
	}
}
